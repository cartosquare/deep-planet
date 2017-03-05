#include <opencv2/core/core.hpp>

#include <fstream>  // NOLINT(readability/streams)
#include <iostream>  // NOLINT(readability/streams)
#include <string>
#include <utility>
#include <vector>

#include "caffe/data_layers.hpp"
#include "caffe/layer.hpp"
#include "caffe/util/benchmark.hpp"
#include "caffe/util/io.hpp"
#include "caffe/util/math_functions.hpp"
#include "caffe/util/rng.hpp"

// gdal
#include "gdal_priv.h"
#include "cpl_conv.h" // for CPLMalloc()

namespace caffe {
    
    template <typename Dtype>
    DenseTiffDataLayer<Dtype>::~DenseTiffDataLayer<Dtype>() {
        this->JoinPrefetchThread();
    }
    
    template <typename Dtype>
    void DenseTiffDataLayer<Dtype>::DataLayerSetUp(const vector<Blob<Dtype>*>& bottom,
                                                   const vector<Blob<Dtype>*>& top) {
        GDALAllRegister();
        
        string root_folder = this->layer_param_.dense_tiff_data_param().root_folder();
        
        // Read the file with filenames and labels
        const string& source = this->layer_param_.dense_tiff_data_param().source();
        LOG(INFO) << "Opening file " << source;
        std::ifstream infile(source.c_str());
        string filename;
        string label_filename;
        while (infile >> filename >> label_filename) {
            lines_.push_back(std::make_pair(filename, label_filename));
        }
        
        if (this->layer_param_.dense_tiff_data_param().shuffle()) {
            // randomly shuffle data
            LOG(INFO) << "Shuffling data";
            const unsigned int prefetch_rng_seed = caffe_rng_rand();
            prefetch_rng_.reset(new Caffe::RNG(prefetch_rng_seed));
            ShuffleImages();
        }
        LOG(INFO) << "A total of " << lines_.size() << " examples.";
        
        lines_id_ = 0;
        // Check if we would need to randomly skip a few data points
        if (this->layer_param_.dense_tiff_data_param().rand_skip()) {
            unsigned int skip = caffe_rng_rand() %
            this->layer_param_.dense_tiff_data_param().rand_skip();
            LOG(INFO) << "Skipping first " << skip << " data points.";
            CHECK_GT(lines_.size(), skip) << "Not enough points to skip";
            lines_id_ = skip;
        }
        
        // Read an GeoTiff, and use it to initialize the top blobs.
        GDALDataset* dataset = (GDALDataset*)GDALOpen((root_folder + lines_[lines_id_].first).c_str(), GA_ReadOnly);
        CHECK(dataset == 0) << "Open file " << lines_[lines_id_].first << " fail";
        const int channels = dataset->GetRasterCount();
        const int width = dataset->GetRasterXSize();
        const int height = dataset->GetRasterYSize();
        GDALClose(dataset);
        
        // sanity check label image
        cv::Mat cv_lab = ReadImageToCVMat(root_folder + lines_[lines_id_].second, 0, 0, false, true);
        CHECK(cv_lab.channels() == 1) << "Can only handle grayscale label images";
        CHECK(cv_lab.rows == height && cv_lab.cols == width) << "Input and label "
        << "image heights and widths must match";
        
        const int batch_size = this->layer_param_.dense_tiff_data_param().batch_size();
        
        // reshape training data blobs
        top[0]->Reshape(batch_size, channels, height, width);
        this->prefetch_data_.Reshape(batch_size, channels, height, width);
        this->transformed_data_.Reshape(1, channels, height, width);
        
        // similarly reshape label data blobs
        top[1]->Reshape(batch_size, 1, height, width);
        this->prefetch_label_.Reshape(batch_size, 1, height, width);
        this->transformed_label_.Reshape(1, 1, height, width);
        
        LOG(INFO) << "output data size: " << top[0]->num() << ","
        << top[0]->channels() << "," << top[0]->height() << ","
        << top[0]->width();
    }
    
    template <typename Dtype>
    void DenseTiffDataLayer<Dtype>::ShuffleImages() {
        caffe::rng_t* prefetch_rng =
        static_cast<caffe::rng_t*>(prefetch_rng_->generator());
        shuffle(lines_.begin(), lines_.end(), prefetch_rng);
    }
    
    // This function is used to create a thread that prefetches the data.
    template <typename Dtype>
    void DenseTiffDataLayer<Dtype>::InternalThreadEntry() {
        CPUTimer batch_timer;
        batch_timer.Start();
        
        double read_time = 0;
        CPUTimer timer;
        CHECK(this->prefetch_data_.count());
        CHECK(this->transformed_data_.count());
        
        DenseTiffDataParameter dense_tiff_data_param = this->layer_param_.dense_tiff_data_param();
        const int batch_size = dense_tiff_data_param.batch_size();

        string root_folder = dense_tiff_data_param.root_folder();
        // Reshape on single input batches for inputs of varying dimension.
        if (batch_size == 1) {
            GDALDataset* dataset = (GDALDataset*)GDALOpen((root_folder + lines_[lines_id_].first).c_str(), GA_ReadOnly);
            CHECK(dataset == 0) << "Open file " << lines_[lines_id_].first << " fail";
            
            const int channels = dataset->GetRasterCount();
            const int width = dataset->GetRasterXSize();
            const int height = dataset->GetRasterYSize();
            
            this->prefetch_data_.Reshape(1, channels, height, width);
            this->transformed_data_.Reshape(1, channels, height, width);
            
            this->prefetch_label_.Reshape(1, 1, height, width);
            this->transformed_label_.Reshape(1, 1, height, width);
            
            GDALClose(dataset);
        }
        
        Dtype* prefetch_data = this->prefetch_data_.mutable_cpu_data();
        Dtype* prefetch_label = this->prefetch_label_.mutable_cpu_data();
        
        // datum scales
        const int lines_size = lines_.size();
        for (int item_id = 0; item_id < batch_size; ++item_id) {
            // get a blob
            timer.Start();
            CHECK_GT(lines_size, lines_id_);
            
            // open geotiff data
            GDALDataset* dataset = (GDALDataset*)GDALOpen((root_folder + lines_[lines_id_].first).c_str(), GA_ReadOnly);
            CHECK(dataset == 0) << "Open file " << lines_[lines_id_].first << " fail";
            
            // open label data
            cv::Mat cv_lab = ReadImageToCVMat(root_folder + lines_[lines_id_].second, 0, 0, false, true);
            CHECK(cv_lab.data) << "Could not load " << lines_[lines_id_].second;
            read_time += timer.MicroSeconds();
            
            
            // Apply transformations to the image
            int offset = this->prefetch_data_.offset(item_id);
            this->transformed_data_.set_cpu_data(prefetch_data + offset);
            this->data_transformer_->Transform(dataset, &(this->transformed_data_));
            // close dataset
            GDALClose(dataset);
            
            // transform label the same way
            int label_offset = this->prefetch_label_.offset(item_id);
            this->transformed_label_.set_cpu_data(prefetch_label + label_offset);
            this->data_transformer_->Transform(cv_lab, &this->transformed_label_, true);
            
            
            // go to the next iter
            lines_id_++;
            if (lines_id_ >= lines_size) {
                // We have reached the end. Restart from the first.
                DLOG(INFO) << "Restarting data prefetching from start.";
                lines_id_ = 0;
                if (this->layer_param_.dense_tiff_data_param().shuffle()) {
                    ShuffleImages();
                }
            }
        }

        batch_timer.Stop();
        DLOG(INFO) << "Prefetch batch: " << batch_timer.MilliSeconds() << " ms.";
        DLOG(INFO) << "     Read time: " << read_time / 1000 << " ms.";
    }
    
    INSTANTIATE_CLASS(DenseTiffDataLayer);
    REGISTER_LAYER_CLASS(DenseTiffData);
    
}  // namespace caffe
