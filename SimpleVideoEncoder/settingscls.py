from os import path
from os.path import abspath
import pickle 

class Settings:
    
    
    default_encode_param = '-c:v libx264  -f mp4'
    ffmpeg_location = abspath(__file__).rsplit('\\',1)[0] + '\\ffmpeg.exe'
    is_two_pass = True
    is_cryterium_on = False
    limit_size_mb = str(700)
    is_use_own_encode_param = False
    own_encode_param = '-c:v libx264  -f mp4'
    res_x = str(854)
    res_y = str(480)
    bitrate = str(1000)
    is_keep_ratio = False
    is_keep_resolution = False
    is_upscale_forbidden = False
    bitrate_choise = 0

    def __init__( self, data_file_name ):
        self.DATA_FILE_NAME = data_file_name

    
    def read_settings(self):
        
       
        try:  
            with open(self.DATA_FILE_NAME, 'rb') as f:  
                self.my_persistent_data = pickle.load(f)  
        except Exception:  
            self.my_persistent_data = {}  

        if self.my_persistent_data:
            try: 
                self.ffmpeg_location = self.my_persistent_data['ffmpeg_location']
                self.is_two_pass = bool(self.my_persistent_data['is_two_pass'])
                self.is_cryterium_on = bool(self.my_persistent_data['is_cryterium_on'])
                self.limit_size_mb = float(self.my_persistent_data['limit_size_mb'])
                self.is_use_own_encode_param = bool(self.my_persistent_data['is_use_own_encode_param'])
                self.own_encode_param = self.my_persistent_data['own_encode_param']
                self.res_x = self.my_persistent_data['res_x']
                self.res_y = self.my_persistent_data['res_y']
                self.bitrate = self.my_persistent_data['bitrate']
                self.is_keep_ratio = self.my_persistent_data['is_keep_ratio']
                self.is_keep_resolution = self.my_persistent_data['is_keep_resolution']
                self.is_upscale_forbidden = self.my_persistent_data['is_upscale_forbidden']
                self.bitrate_choise = self.my_persistent_data['bitrate_choise']
            
            except:
                return
   


    def write_settings(self):

        try:  
            with open(self.DATA_FILE_NAME, 'rb') as f:  
                self.my_persistent_data = pickle.load(f)  
        except Exception:  
            self.my_persistent_data = {}  


        self.my_persistent_data.update(
                        {
                        'ffmpeg_location' : self.ffmpeg_location,
                        'is_two_pass' : self.is_two_pass,
                        'is_cryterium_on' : self.is_cryterium_on,
                        'limit_size_mb' : self.limit_size_mb,
                        'is_use_own_encode_param' : self.is_use_own_encode_param,
                        'own_encode_param' : self.own_encode_param,
                        'res_x' : self.res_x,
                        'res_y' : self.res_y,
                        'bitrate' : self.bitrate,
                        'is_keep_resolution' : self.is_keep_resolution,
                        'is_keep_ratio' : self.is_keep_ratio,
                        'is_upscale_forbidden' : self.is_upscale_forbidden,
                        'bitrate_choise' : self.bitrate_choise                        
                        })

        with open(self.DATA_FILE_NAME, 'wb') as f:  
             pickle.dump(self.my_persistent_data, f)  


