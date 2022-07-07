import os
from os import path
from os.path import abspath
import subprocess
from subprocess import Popen, run, STDOUT, PIPE
import wx 
import datetime
import time
from multiprocessing import Queue

from proj_constants import *

class FFmpegWrapper:
    file_list = [] 
    output_file_list = []
    move_file_list = []
    movie_duration = []
    current_processed_file_number = 0
    is_keep_ratio = False
    is_keep_resolution = False
    bitrate = '1000'
    resX = '1920'
    resY = '1080'
    is_upscale_forbidden = False
    bitrate_choise = 0
    ffmpeg_location = ''
    limit_size_mb = str(700)
    status = ST_WAITING
    queue = Queue()
    timer_period = 200
    DATA_FILE_PATH = ''
    own_encode_param =  '-c:v libx264  -f mp4'
    is_use_own_encode_param =  False
    default_encode_param =  '-c:v libx264  -f mp4'
    is_two_pass =  True
    is_cryterium_on = False
    text_status = ''
    EncEndEvent, EVT_ENC_END_EVENT = wx.lib.newevent.NewEvent()
    FileEncEvent, EVT_FILE_END_EVENT = wx.lib.newevent.NewEvent()
    last_enc_result = ''
    process = None

    def get_last_enc_result():
        return self.last_enc_result


    def clear_last_enc_result():
        self.last_enc_result = ''


    def clear_movies_data(self):
        self.file_list = [] 
        self.output_file_list = []
        self.move_file_list = []
        self.movie_duration = []
        self.current_processed_file_number = 0   
 
    def get_text_status(self):
        return self.text_status

    def set_text_status(self, text_status):
        self.text_status = text_status

    def set_own_encode_param(self, own_encode_param):
        self.own_encode_param = own_encode_param


    def set_is_use_own_encode_param(self, is_use_own_encode_param):
        self.is_use_own_encode_param = is_use_own_encode_param


    def set_default_encode_param(self, default_encode_param):
        self.default_encode_param = default_encode_param


    def set_is_two_pass(self, is_two_pass):
        self.is_two_pass = is_two_pass


    def set_is_cryterium_on(self, is_cryterium_on):
        self.is_cryterium_on = is_cryterium_on


    def set_DATA_FILE_PATH(self, DATA_FILE_PATH):
        self.DATA_FILE_PATH = DATA_FILE_PATH


    def set_timer_period(self, timer_period):
        self.timer_period = timer_period


    def set_limit_size_mb(self, limit_size_mb):
        self.limit_size_mb = limit_size_mb


    def set_ffmpeg_location(self, ffmpeg_location):
        self.ffmpeg_location = ffmpeg_location


    def set_bitrate_choise(self, bitrate_choise):
        self.bitrate_choise = bitrate_choise


    def determine_bitrate(self):
        if self.bitrate_choise == 3:
            return
        elif self.bitrate_choise == 0:
            resx_i = int(self.resX)
            resy_i = int(self.resY)
            self.bitrate = str(int((2 * resx_i * resy_i + 180000)/2000))
        elif self.bitrate_choise == 1:
            resx_i = int(self.resX)
            resy_i = int(self.resY)
            self.bitrate = str(int((2 * resx_i * resy_i + 180000)/1000))
            pass
        elif self.bitrate_choise == 2:
            resx_i = int(self.resX)
            resy_i = int(self.resY)
            self.bitrate = str(int((2 * resx_i * resy_i + 180000)/500))
            pass


    def correct_resolution(self, filepath):
        
        if (not self.is_keep_ratio) and (not self.is_keep_resolution) and (not self.is_upscale_forbidden):
            return

        util_path = self.ffmpeg_location
        cmd = util_path + ' -i ' + '\"' + str(filepath) + '\"' + ' -hide_banner'
        output = run(cmd, stdout=PIPE, stderr=STDOUT, text=True)
        output_info = str(output)
    
        fps_pos = output_info.find(' fps, ')
        if fps_pos < 30: # 30 - garanted num of chars before
            return 

        vid_pos = output_info.rfind('Video: ')
        x_pos = output_info.rfind('x', vid_pos, fps_pos)
        x_left = output_info.rfind(', ', x_pos - 7, x_pos)
        x_right = output_info.find(' ', x_pos, x_pos + 7)

        if (vid_pos == -1) or (x_pos == -1) or (x_left == -1) or (x_right == -1):
            return

        if output_info[x_right - 1] == ',':
            x_right -= 1

        resx_s = output_info[x_left + 2 : x_pos]
        resy_s = output_info[x_pos + 1 : x_right]
        
        if (self.is_keep_resolution) or (self.is_upscale_forbidden and (int(resx_s) < int(self.resX))):
            self.resX = resx_s
            self.resY = resy_s
            return

        if self.is_keep_ratio:
            resx_f = float(resx_s)
            resy_f = float(resy_s)

            aspect = resx_f / resy_f
            calc_resy = int(float(self.resX) / aspect)
            if calc_resy % 2 != 0:
                if (calc_resy + 1) % 4 == 0:
                    calc_resy += 1
                else:
                    calc_resy -= 1

            self.resY = str(calc_resy)
            return


    def set_bitrate_choise(self, bitrate_choise = 0):
        self.bitrate_choise = bitrate_choise


    def set_is_upscale_forbidden(self, is_upscale_forbidden = False):
        self.is_upscale_forbidden = is_upscale_forbidden


    def set_bitrate(self, bitrate='1000'):
        self.bitrate = bitrate


    def set_resX(self, resX='1920'):
        self.resX = resX


    def set_resY(self, resY='1080'):
        self.resY = resY


    def set_keep_resolution(self, keep_resolution_flag = False):
        self.is_keep_resolution = keep_resolution_flag


    def set_keep_ratio(self, keep_ratio_flag = False):
        self.is_keep_ratio = keep_ratio_flag


    def __init__(self, parent):
        self.parent = parent


    def is_there_sens_to_convert(self, filepath, movie_duration=[]):
        '''
        Function check is there sense to convert file
        return bool
        '''
        
        util_path = self.ffmpeg_location
        cmd = util_path + ' -i ' + '\"' + str(filepath) + '\"' + ' -hide_banner'
        output = run(cmd, stdout=PIPE, stderr=STDOUT, text=True)
        output_info = str(output)
    
        dur_pos = output_info.find('Duration:')
        if dur_pos == -1:
            return True

        dots_pos = output_info.find(':', dur_pos)
        dots_pos = output_info.find(':', dots_pos + 1)
        output_info = output_info[dots_pos - 2 : dots_pos + 6]
                
        duration_Hours = float(output_info[:2]) + float(output_info[3:5]) / 60 + float(output_info[6:8]) / 3600
        movie_duration.append(float(duration_Hours))

        file_size = os.path.getsize(filepath)
        file_size_GB = file_size / (1024 * 1024 * 1024)
    

        if not file_size_GB:
            return False
                
        return not (file_size_GB / duration_Hours < (float(self.limit_size_mb) / 1000))
        

    def convert_one_file(self, input_file_path, output_file_path):
        '''
            Converts one file, returns success
        '''
        
        util_path = self.ffmpeg_location

        def send_time_script():
            while (not self.status == ST_STOPPED):
                line = self.process.stderr.readline()
                self.process.stderr.flush()
                if line[0:6] == 'frame=':
                    self.queue.put(line)
                    time.sleep(self.timer_period / 1000)       # ms to s
                if self.process.poll() == 0:
                    break
            self.text_status = ''

        encode_param = self.own_encode_param if self.is_use_own_encode_param else self.default_encode_param
        self.correct_resolution(input_file_path)
        self.determine_bitrate()

        if self.status == ST_STOPPED: 
            self.text_status = ''
            return False

        if self.is_two_pass:
            try:
                string = util_path + ' -y -i ' + '\"' + input_file_path + '\" '
                string +=  encode_param + ' -b:v ' + self.bitrate + 'K' + ' -pass 1' + ' -vf scale=' + self.resX + ':' + self.resY 
                string += ' -passlogfile ' + self.DATA_FILE_PATH + 'path1log.log ' + self.DATA_FILE_PATH + 'NULL  -hide_banner'
                self.text_status = 'Encoding progress (1 pass):'
                self.status = ST_1PASS
                time_enc_start = datetime.datetime.now()
                self.process = Popen(string, stdout=None, stderr=PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                send_time_script()
            except:
                return False
                if self.status == ST_STOPPED: 
                    self.text_status = ''
                    return False
            try:
                string = util_path + ' -y -i ' + '\"' + input_file_path + '\" '
                string +=  encode_param + ' -b:v ' + self.bitrate + 'K' + ' -pass 2' + ' -vf scale=' + self.resX + ':' + self.resY + ' ' 
                string += ' -passlogfile ' + self.DATA_FILE_PATH + 'path1log.log ' + '\"' + output_file_path + '\" -hide_banner' 
                self.text_status = 'Encoding progress (2 pass):'
                self.status = ST_2PASS
                time_enc_start = datetime.datetime.now()
                self.process = Popen(string, stdout=None, stderr=PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                send_time_script()
            except:
                return False
        else:
            try:
                if self.status == ST_STOPPED: 
                    self.text_status = ''
                    return False
                string = util_path + ' -y ' + '-i ' + '\"' + input_file_path + '\" '
                string +=  encode_param + ' -b:v ' + self.bitrate + 'K' + ' -vf scale=' + self.resX + ':' + self.resY + ' ' 
                string +=   '\"' + output_file_path + '\" -hide_banner' 
                self.text_status = 'Encoding progress:'
                self.status = ST_ENCODING
                time_enc_start = datetime.datetime.now()
                self.process = Popen(string, stdout=None, stderr=PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                send_time_script()
                
                #print(self.process.pid)
            except:
                return False
        return True


    def create_directory_if_needed(self,filepath:str):
        dirpath = filepath.rsplit('\\', 1)[0]
        if not os.path.isdir(dirpath):
            os.makedirs(dirpath)


    def delete_garbage_after(self,file_path=''):
        if file_path:        
            dirpath = file_path.rsplit('\\', 1)[0]
        else:
            dirpath = self.DATA_FILE_PATH

        for root, dirs, files in os.walk(dirpath):
            for name in files:
                temp_str = os.path.join(root, name)
                if 'NULL' in temp_str or 'path1log' in temp_str:
                    os.remove(temp_str)

            for name in dirs:
                temp_str = os.path.join(root, name)

                for root1, dirs1, files1 in os.walk(temp_str):
                    if (not files1) and (not dirs1):
                        os.rmdir(temp_str)
                    break
                   
            break


    def converting_thread(self):
        util_path = self.ffmpeg_location


        while self.current_processed_file_number < len(self.file_list):
            if self.status == ST_STOPPED: 
                self.text_status = ''
                return
            if (self.is_there_sens_to_convert(self.file_list[self.current_processed_file_number], self.movie_duration) or (not self.is_cryterium_on)):
                self.create_directory_if_needed(self.output_file_list[self.current_processed_file_number])
                movie_duration_str = str(self.movie_duration[0])

                self.last_enc_result = 'next'
                wx.PostEvent(self.parent, self.FileEncEvent())


                if self.convert_one_file(self.file_list[self.current_processed_file_number], self.output_file_list[self.current_processed_file_number]):
                    if self.status == ST_STOPPED:
                        self.text_status = ''
                        return
                    self.create_directory_if_needed(self.move_file_list[self.current_processed_file_number])
                    while os.path.isfile(self.move_file_list[self.current_processed_file_number]):
                        self.move_file_list[self.current_processed_file_number] = self.insert(self.move_file_list[self.current_processed_file_number], '+', len(self.move_file_list[self.current_processed_file_number]) - 4)
                    os.rename(self.file_list[self.current_processed_file_number], self.move_file_list[self.current_processed_file_number])
                    self.last_enc_result = '   <--- Done'
                    self.processed_file_number = self.current_processed_file_number
                    wx.PostEvent(self.parent, self.FileEncEvent())
                    self.delete_garbage_after()
                else:
                    if self.status == ST_STOPPED:
                        self.text_status = ''
                        return
                    else:
                        self.last_enc_result = '   <--- Error'
                        self.processed_file_number = self.current_processed_file_number
                        wx.PostEvent(self.parent, self.FileEncEvent())
                    pass
            else:
                self.create_directory_if_needed(self.output_file_list[self.current_processed_file_number])
                while os.path.isfile(self.output_file_list[self.current_processed_file_number]):
                    self.output_file_list[self.current_processed_file_number] = self.insert(self.output_file_list[self.current_processed_file_number], '+', len(self.output_file_list[self.current_processed_file_number]) - 4)
                os.rename(self.file_list[self.current_processed_file_number], self.output_file_list[self.current_processed_file_number])
                self.last_enc_result = '   <--- No sense to convert'
                self.processed_file_number = self.current_processed_file_number
                wx.PostEvent(self.parent, self.FileEncEvent())

        
            self.current_processed_file_number += 1

        self.current_processed_file_number += 1
        self.text_status = ''
        self.status = ST_FINISHED
        
        self.last_enc_result = ''
        wx.PostEvent(self.parent, self.FileEncEvent())
        
        self.file_list = []
        self.output_file_list = []
        self.move_file_list = []
        
        wx.PostEvent(self.parent, self.EncEndEvent())


    def insert(self, source_str, insert_str, pos):
        return source_str[:pos] + insert_str + source_str[pos:]