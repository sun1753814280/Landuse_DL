#!/usr/bin/env python
# Filename: get_sub_images_multi_files 
"""
introduction:  extract sub-images and sub-labels for one or multi given shape file (training polygons)

authors: Huang Lingcao
email:huanglingcao@gmail.com
add time: 25 December, 2019
modified on 19 January, 2021
"""

import os,sys
from optparse import OptionParser

code_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, code_dir)
import parameters

import utility.get_valid_percent_entropy as get_valid_percent_entropy

import basic_src.io_function as io_function
import datasets.raster_io as raster_io
import time

def get_subImage_subLabel_one_shp(get_subImage_script,all_train_shp, buffersize, dstnodata, rectangle_ext, train_shp,
                                  input_image_dir, file_pattern = None, process_num=1):
    if file_pattern is None:
        file_pattern = '*.tif'

    command_string = get_subImage_script + ' -f ' + all_train_shp + ' -b ' + str(buffersize) + ' -e ' + file_pattern + \
                    ' -o ' + os.getcwd() + ' -n ' + str(dstnodata)  + ' -p ' + str(process_num) \
                     + ' ' + rectangle_ext + ' ' + train_shp + ' '+ input_image_dir

    # ${eo_dir}/sentinelScripts/get_subImages.py -f ${all_train_shp} -b ${buffersize} -e .tif \
    #             -o ${PWD} -n ${dstnodata} -r ${train_shp} ${input_image_dir}

    # status, result = basic.exec_command_string(command_string)  # this will wait command finished
    # os.system(command_string + "&")  # don't know when it finished
    res = os.system(command_string )      # this work
    if res != 0:
        sys.exit(1)

def main(options, args):
    print("%s : extract sub-images and sub-labels for a given shape file (training polygons)" %
          os.path.basename(sys.argv[0]))

    para_file = args[0]
    if os.path.isfile(para_file) is False:
        raise IOError('File %s not exists in current folder: %s' % (para_file, os.getcwd()))

    get_subImage_script = os.path.join(code_dir, 'datasets', 'get_subImages.py')
    SECONDS = time.time()

    # get name of training areas
    multi_training_regions = parameters.get_string_list_parameters_None_if_absence(para_file, 'training_regions')
    if multi_training_regions is None or len(multi_training_regions) < 1:
        raise ValueError('No training area is set in %s'%para_file)

    # multi_training_files = parameters.get_string_parameters_None_if_absence(para_file, 'multi_training_files')

    dstnodata = parameters.get_string_parameters(para_file, 'dst_nodata')
    buffersize = parameters.get_string_parameters(para_file, 'buffer_size')
    rectangle_ext = parameters.get_string_parameters(para_file, 'b_use_rectangle')
    process_num = parameters.get_digit_parameters(para_file,'process_num', 'int')

    if os.path.isfile('sub_images_labels_list.txt'):
        io_function.delete_file_or_dir('sub_images_labels_list.txt')

    subImage_dir = parameters.get_string_parameters_None_if_absence(para_file,'input_train_dir')
    subLabel_dir = parameters.get_string_parameters_None_if_absence(para_file,'input_label_dir')

    # loop each training regions
    for idx, area_ini in enumerate(multi_training_regions):

        input_image_dir = parameters.get_directory_None_if_absence(area_ini, 'input_image_dir')

        # it is ok consider a file name as pattern and pass it the following functions to get file list
        input_image_or_pattern = parameters.get_string_parameters(area_ini, 'input_image_or_pattern')

        all_train_shp = parameters.get_file_path_parameters_None_if_absence(area_ini, 'training_polygons')
        train_shp = parameters.get_string_parameters(area_ini, 'training_polygons_sub')

        # get subImage and subLabel for one training polygons
        print('extract training data from image folder (%s) and polgyons (%s)' % (input_image_dir, train_shp))
        get_subImage_subLabel_one_shp(get_subImage_script,all_train_shp, buffersize, dstnodata, rectangle_ext, train_shp,
                                      input_image_dir, file_pattern=input_image_or_pattern, process_num=process_num)


    # check black sub-images or most part of the sub-images is black (nodata)
    new_sub_image_label_list = []
    delete_sub_image_label_list = []
    subImage_dir_delete = subImage_dir + '_delete'
    subLabel_dir_delete = subLabel_dir + '_delete'
    io_function.mkdir(subImage_dir_delete)
    io_function.mkdir(subLabel_dir_delete)
    get_valid_percent_entropy.plot_valid_entropy(subImage_dir)
    with open('sub_images_labels_list.txt','r') as f_obj:
        lines = f_obj.readlines()
        for line in lines:
            image_path, label_path = line.strip().split(':')
            # valid_per = raster_io.get_valid_pixel_percentage(image_path)
            valid_per, entropy = raster_io.get_valid_percent_shannon_entropy(image_path)    # base=10
            if valid_per > 80 and entropy >= 0.5:
                new_sub_image_label_list.append(line)
            else:
                delete_sub_image_label_list.append(line)
                io_function.movefiletodir(image_path,subImage_dir_delete)
                io_function.movefiletodir(label_path,subLabel_dir_delete)
    if len(delete_sub_image_label_list) > 0:
        with open('sub_images_labels_list.txt', 'w') as f_obj:
            for line in new_sub_image_label_list:
                f_obj.writelines(line)

    # check weather they have the same subImage and subLabel
    sub_image_list = io_function.get_file_list_by_pattern(subImage_dir,'*.tif')
    sub_label_list = io_function.get_file_list_by_pattern(subLabel_dir,'*.tif')
    if len(sub_image_list) != len(sub_label_list):
        raise ValueError('the count of subImage (%d) and subLabel (%d) is different'
                         %(len(sub_image_list),len(sub_label_list)))

    # save brief information of sub-images
    height_list = []
    width_list = []
    band_count = 0
    dtype = 'unknown'
    for line in new_sub_image_label_list:
        image_path, label_path = line.strip().split(':')
        height, width, band_count, dtype = raster_io.get_height_width_bandnum_dtype(image_path)
        height_list.append(height)
        width_list.append(width)
    # save info to file, if it exists, it will be overwritten
    img_count = len(new_sub_image_label_list)
    with open('sub_images_patches_info.txt','w') as f_obj:
        f_obj.writelines('information of sub-images: \n')
        f_obj.writelines('number of sub-images : %d \n' % img_count)
        f_obj.writelines('band count : %d \n'%band_count)
        f_obj.writelines('data type : %s \n'%dtype)
        f_obj.writelines('maximum width and height: %d, %d \n'% (max(width_list), max(height_list)) )
        f_obj.writelines('minimum width and height: %d, %d \n'% (min(width_list), min(height_list)) )
        f_obj.writelines('mean width and height: %.2f, %.2f \n\n'% (sum(width_list)/img_count, sum(height_list)/img_count))


    duration= time.time() - SECONDS
    os.system('echo "$(date): time cost of getting sub images and labels: %.2f seconds">>time_cost.txt'%duration)

if __name__ == '__main__':

    usage = "usage: %prog [options] para_file "
    parser = OptionParser(usage=usage, version="1.0 2021-01-19")
    parser.description = 'Introduction: extract sub-images and sub-labels '

    (options, args) = parser.parse_args()
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(2)

    main(options, args)

