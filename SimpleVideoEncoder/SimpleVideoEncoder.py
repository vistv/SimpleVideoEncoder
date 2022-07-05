import os
from os import path
from os.path import abspath
import time
import sched
import threading 
import wx 
import wx.xrc
import subprocess
from subprocess import Popen, run, STDOUT, PIPE
from multiprocessing import Queue 
import datetime
import wx.html
import psutil
import wx.lib.newevent

from aboutcls import About 
from settingscls import Settings
from helpcls import Help
from settingsdialogcls import SettingsDialog
from ffmpegwrapper import FFmpegWrapper

from proj_constants import *


class SimpleVideoEncoder(wx.Frame):

    EncEndEvent, EVT_ENC_END_EVENT = wx.lib.newevent.NewEvent()
    DATA_FILE_NAME = path.expandvars(r'%APPDATA%\SimpleVideoEncoder\persistent_data.pickle')        
    DATA_FILE_PATH = DATA_FILE_NAME.rsplit('\\', 1)[0] + '\\'
        

    settings = Settings(DATA_FILE_NAME)
    
    
    process = None
    queue = Queue()
     
    helpframe = None
    aboutframe = None
    timer_period = 200 #ms
    status = ST_WAITING
    before_pause_status = ST_ENCODING
    

    def __init__(self, parent):
        super().__init__()

        self.ffmpg_wrp = FFmpegWrapper(self)
        
        self.build_ui(parent)
        self.connect_events()

        self.ffmpg_wrp.create_directory_if_needed(self.DATA_FILE_NAME)
        self.settings.read_settings()
        self.res_x.SetValue(self.settings.res_x)
        self.res_y.SetValue(self.settings.res_y)
        self.bitrate.SetValue(self.settings.bitrate)

        self.prepare_waiting_interface()

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_timer, self.timer)


    def build_ui(self, parent):
  
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = 'Simple video encoder', pos = wx.DefaultPosition, size = wx.Size( 890,520 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )
        
        self.SetSizeHints( wx.Size( 890,520 ), wx.DefaultSize )
        
        icon = wx.Icon()
        icon.CopyFromBitmap(wx.Bitmap("vico.ico", wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)

        self.m_statusBar2 = self.CreateStatusBar( 1, wx.STB_SIZEGRIP, wx.ID_ANY )
        self.m_statusBar2.SetStatusText('   Let\'s start')

        self.m_menubar2 = wx.MenuBar( 0 )
        
        filemenu = wx.Menu()
        self.menuitem_openfile = filemenu.Append(ID_OPEN_FILES, 'Choose File(s)\tCtrl+O', 'Choose videofile(s) to encode')
        self.menuitem_opendirectory = filemenu.Append(ID_OPEN_DIRECTORY, 'Choose directory\tCtrl+D', 'Choose directory to encode set of videofiles')
        self.menuitem_exit = filemenu.Append(wx.ID_EXIT, 'Exit\tCtrl+Q', 'Exit from the application')

        runmenu = wx.Menu()
        self.menuitem_encode = runmenu.Append(ID_RUN, 'Encode\tCtrl+E', 'Encode selected videofiles')
        self.menuitem_pause = runmenu.Append(ID_PAUSE, 'Pause\tCtrl+P', 'Pause/Continue encoding process')
        self.menuitem_stop = runmenu.Append(ID_STOP, 'Stop\tCtrl+B', 'Stop encoding')
 
        helpmenu = wx.Menu()
        self.menuitem_help = helpmenu.Append(ID_HELP, 'Help\tCtrl+H', 'Short manual')
        self.menuitem_about = helpmenu.Append(ID_ABOUT, 'About\tCtrl+A', 'About the application')

        self.m_menubar2.Append(filemenu, '&File')
        self.m_menubar2.Append(runmenu, '&Action')
        self.m_menubar2.Append(helpmenu, '&Help')
        
        self.SetMenuBar( self.m_menubar2 )
        
        self.Bind(wx.EVT_MENU, self.choose_files, self.menuitem_openfile)
        self.Bind(wx.EVT_MENU, self.choose_dir, self.menuitem_opendirectory)
        self.Bind(wx.EVT_MENU, self.on_closing, self.menuitem_exit)

        self.Bind(wx.EVT_MENU, self.on_run, self.menuitem_encode)
        self.Bind(wx.EVT_MENU, self.on_pause, self.menuitem_pause)
        self.Bind(wx.EVT_MENU, self.on_stop, self.menuitem_stop)

        self.Bind(wx.EVT_MENU, self.on_help, self.menuitem_help)
        self.Bind(wx.EVT_MENU, self.on_about, self.menuitem_about)
        
             
        
        bSizer7 = wx.BoxSizer( wx.VERTICAL )

        self.m_panel4 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer9 = wx.BoxSizer( wx.HORIZONTAL )

        gSizer5 = wx.GridSizer( 2, 6, 0, 0 )

        self.bt_dir = wx.Button( self.m_panel4, wx.ID_ANY, u"Open Directory", wx.DefaultPosition, wx.DefaultSize, 0 )
        gSizer5.Add( self.bt_dir, 0, wx.ALL|wx.EXPAND, 5 )

        self.m_checkBox_keep_resolution = wx.CheckBox( self.m_panel4, wx.ID_ANY, u"Keep resolution", wx.DefaultPosition, wx.DefaultSize, 0 )
        gSizer5.Add( self.m_checkBox_keep_resolution, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

        self.m_staticText9 = wx.StaticText( self.m_panel4, wx.ID_ANY, u"Resolution X:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText9.Wrap( -1 )

        gSizer5.Add( self.m_staticText9, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5 )

        self.res_x = wx.TextCtrl( self.m_panel4, wx.ID_ANY, u"854", wx.DefaultPosition, wx.DefaultSize, wx.TE_CENTER )
        gSizer5.Add( self.res_x, 0, wx.ALL|wx.EXPAND, 5 )

        self.m_staticText10 = wx.StaticText( self.m_panel4, wx.ID_ANY, u"Bitrate (kBps):", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText10.Wrap( -1 )

        gSizer5.Add( self.m_staticText10, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5 )

        self.bitrate = wx.TextCtrl( self.m_panel4, wx.ID_ANY, u"1000", wx.DefaultPosition, wx.DefaultSize, wx.TE_CENTER )
        self.bitrate.SetMaxSize( wx.Size( 50,-1 ) )

        gSizer5.Add( self.bitrate, 0, wx.ALL|wx.EXPAND, 5 )

        self.bt_input = wx.Button( self.m_panel4, wx.ID_ANY, u"Open file(s)", wx.DefaultPosition, wx.DefaultSize, 0 )
        gSizer5.Add( self.bt_input, 0, wx.ALL|wx.EXPAND, 5 )

        self.m_checkBox_keep_ratio = wx.CheckBox( self.m_panel4, wx.ID_ANY, u"Keep Aspect ratio", wx.DefaultPosition, wx.DefaultSize, 0 )
        gSizer5.Add( self.m_checkBox_keep_ratio, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 5 )

        self.m_staticText11 = wx.StaticText( self.m_panel4, wx.ID_ANY, u"Resolution Y:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText11.Wrap( -1 )

        gSizer5.Add( self.m_staticText11, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5 )

        self.res_y = wx.TextCtrl( self.m_panel4, wx.ID_ANY, u"480", wx.DefaultPosition, wx.DefaultSize, wx.TE_CENTER )
        gSizer5.Add( self.res_y, 0, wx.ALL|wx.EXPAND, 5 )

        self.m_button_help = wx.Button( self.m_panel4, wx.ID_ANY, u"Help", wx.DefaultPosition, wx.DefaultSize, 0 )
        gSizer5.Add( self.m_button_help, 1, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5 )

        self.setting_butt = wx.Button( self.m_panel4, wx.ID_ANY, u"Setting", wx.DefaultPosition, wx.DefaultSize, 0 )
        gSizer5.Add( self.setting_butt, 0, wx.ALL|wx.EXPAND, 5 )


        bSizer9.Add( gSizer5, 5, wx.EXPAND, 5 )

        self.bt_run = wx.Button( self.m_panel4, wx.ID_ANY, u"CONVERT", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer9.Add( self.bt_run, 1, wx.ALL|wx.EXPAND, 5 )


        self.m_panel4.SetSizer( bSizer9 )
        self.m_panel4.Layout()
        bSizer9.Fit( self.m_panel4 )
        bSizer7.Add( self.m_panel4, 1, wx.EXPAND|wx.TOP|wx.RIGHT|wx.LEFT, 1 )

        m_main_listBoxChoices = []
        self.m_main_listBox = wx.ListBox( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,300 ), m_main_listBoxChoices, 0 )
        self.m_main_listBox.SetMinSize( wx.Size( -1,300 ) )

        bSizer7.Add( self.m_main_listBox, 5, wx.ALL|wx.EXPAND, 1 )

        self.m_panel2 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer91 = wx.BoxSizer( wx.VERTICAL )

        gSizer2 = wx.GridSizer( 0, 2, 0, 0 )

        self.m_staticText7 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"Encoding progress:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText7.Wrap( -1 )

        gSizer2.Add( self.m_staticText7, 0, wx.ALL|wx.ALIGN_RIGHT, 5 )

        self.m_staticText_timetoend = wx.StaticText( self.m_panel2, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText_timetoend.Wrap( -1 )

        gSizer2.Add( self.m_staticText_timetoend, 0, wx.ALL, 5 )


        bSizer91.Add( gSizer2, 1, wx.EXPAND, 5 )

        bSizer11 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_gauge1 = wx.Gauge( self.m_panel2, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
        self.m_gauge1.SetValue( 0 )
        bSizer11.Add( self.m_gauge1, 1, wx.ALL|wx.EXPAND, 5 )

        self.m_bt_pause = wx.Button( self.m_panel2, wx.ID_ANY, u"Pause", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer11.Add( self.m_bt_pause, 0, wx.ALL, 5 )

        self.m_bt_stop = wx.Button( self.m_panel2, wx.ID_ANY, u"Stop", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer11.Add( self.m_bt_stop, 0, wx.ALL, 5 )


        bSizer91.Add( bSizer11, 1, wx.EXPAND, 5 )


        self.m_panel2.SetSizer( bSizer91 )
        self.m_panel2.Layout()
        bSizer91.Fit( self.m_panel2 )
        bSizer7.Add( self.m_panel2, 1, wx.EXPAND |wx.ALL, 0 )


        self.SetSizer( bSizer7 )
        self.Layout()

        self.Centre( wx.BOTH )



    def connect_events(self):
        self.bt_dir.Bind( wx.EVT_BUTTON, self.choose_dir )
        self.bt_input.Bind( wx.EVT_BUTTON, self.choose_files )
        self.setting_butt.Bind( wx.EVT_BUTTON, self.setting_dialog )
        self.m_button_help.Bind(wx.EVT_BUTTON, self.on_help)
        self.bt_run.Bind( wx.EVT_BUTTON, self.on_run )
        self.Bind( wx.EVT_CLOSE, self.on_closing )
        self.m_bt_pause.Bind( wx.EVT_BUTTON, self.on_pause )
        self.m_bt_stop.Bind( wx.EVT_BUTTON, self.on_stop )
        self.Bind(self.EVT_ENC_END_EVENT, self.on_enc_end)
        self.m_checkBox_keep_resolution.Bind( wx.EVT_CHECKBOX, self.on_check_keep_resolution )
        self.m_checkBox_keep_ratio.Bind( wx.EVT_CHECKBOX, self.on_check_keep_aspect )

  
    def prepare_waiting_interface(self):
        self.bt_input.Enable()
        self.bt_dir.Enable()
        self.bt_run.Disable()
        self.setting_butt.Enable()

        self.m_bt_pause.Disable()
        self.m_bt_stop.Disable()

        self.menuitem_openfile.Enable(enable = True)
        self.menuitem_opendirectory.Enable(enable = True)
        self.menuitem_encode.Enable(enable = False)
        self.menuitem_pause.Enable(enable = False)
        self.menuitem_stop.Enable(enable = False)

        self.m_gauge1.SetValue(0)
        self.m_staticText_timetoend.SetLabel('')
        self.m_staticText7.SetLabel('')


    def prepare_ready_to_encode_interface(self):
        self.bt_input.Enable()
        self.bt_dir.Enable()
        self.bt_run.Enable()
        self.setting_butt.Enable()

        self.m_bt_pause.Disable()
        self.m_bt_stop.Disable()

        self.menuitem_openfile.Enable(enable = True)
        self.menuitem_opendirectory.Enable(enable = True)
        self.menuitem_encode.Enable(enable = True)
        self.menuitem_pause.Enable(enable = False)
        self.menuitem_stop.Enable(enable = False)


    def prepare_encoding_interface(self):
        self.bt_input.Disable()
        self.bt_dir.Disable()
        self.bt_run.Disable()
        self.setting_butt.Disable()

        self.m_bt_pause.Enable()
        self.m_bt_stop.Enable()

        self.menuitem_openfile.Enable(enable = False)
        self.menuitem_opendirectory.Enable(enable = False)
        self.menuitem_encode.Enable(enable = False)
        self.menuitem_pause.Enable(enable = True)
        self.menuitem_stop.Enable(enable = True)

        
    def on_enc_end(self, event):
        self.prepare_waiting_interface()


    def update_timer(self, event):
 
        try:
            full_duration = self.ffmpg_wrp.movie_duration[self.ffmpg_wrp.current_processed_file_number]
        except:
            if self.status == ST_FINISHED:
                self.m_statusBar2.SetStatusText('   Everything is already done!')
            if self.status <= ST_WAITING:
                self.m_statusBar2.SetStatusText('   Waiting')
            if self.status >= ST_ENCODING:
                self.m_statusBar2.SetStatusText('   Starting...')
            if self.status == ST_STOPPED:
                self.m_statusBar2.SetStatusText('   Encoding was stopped.')
            
            self.m_staticText_timetoend.SetLabel('')
            return

        if (not self.queue.empty()) and self.status >= ST_ENCODING:
            line = str(self.queue.get())

            self.m_statusBar2.SetStatusText('  ' + line)
            
            time_ind = line.find('time=')
            if time_ind == -1: return
            dots_pos = line.find(':', time_ind)
            if dots_pos < 5: return
            output_info = line[dots_pos - 2 : dots_pos + 6]
            enc_duration = float(output_info[:2]) + float(output_info[3:5]) / 60 + float(output_info[6:8]) / 3600
            dots_pos = line.find(':', time_ind)
            if dots_pos < 5: return
            output_info = line[dots_pos - 2 : dots_pos + 6]
            enc_duration = float(output_info[:2]) + float(output_info[3:5]) / 60 + float(output_info[6:8]) / 3600

            speed_ind1 = line.find('speed=')
            if speed_ind1 == -1: return
            speed_ind2 = line.find('x', speed_ind1 + 6)
            if speed_ind2 == -1: return
            speed = float(line[speed_ind1 + 6 : speed_ind2])

            if full_duration > enc_duration:
                percent = (enc_duration / full_duration) * 100
                self.m_gauge1.SetValue(percent)
                
                if speed:
                    time_to_encode = ( full_duration - enc_duration ) / speed
                    if self.status == ST_1PASS:
                        time_to_encode += full_duration / speed * 1.5
                    time_enc = str(datetime.timedelta(hours = time_to_encode))

                    self.m_staticText_timetoend.SetLabel('The video will be encoded for: ' + time_enc.split('.')[0])
                
                
        elif self.ffmpg_wrp.current_processed_file_number > len(self.ffmpg_wrp.file_list):
            self.m_statusBar2.SetStatusText('   Everything is already done!')
            self.m_gauge1.SetValue(0)


    def on_help(self, event):
        if not self.helpframe:
            self.helpframe =  Help(self)
        self.helpframe.Show() 


    def on_about(self, event):
        if not self.aboutframe:
            self.aboutframe =  About(self)
        self.aboutframe.Show() 
        

    def setting_dialog(self, event):
        with SettingsDialog(self) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
               self.settings = dlg.get_settings()
   

    def choose_files(self, event):
        '''
            dialog to choose files
        '''
        result = False
   
        fd = None
        dialog = wx.FileDialog(self, "Choose a file", wildcard="Video files | .3g2; *.3gp; *.3gp2; *.3gpp; *.3gpp2; *.asf; *.asx; *.avi; *.bin; *.dat; *.drv; *.f4v; *.flv; *.gtp; *.h264; *.m4v; *.mkv; *.mod; *.moov; *.mov; *.mp4; *.mpeg; *.mpg; *.mts; *.rm; *.rmvb; *.spl; *.srt; *.stl; *.swf; *.ts; *.vcd; *.vid; *.vid; *.vid; *.vob; *.webm; *.wm; *.wmv; *.yuv", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE)
        if dialog.ShowModal() == wx.ID_OK:
            fd = dialog.GetPaths()
        
        if fd:
            self.m_main_listBox.Clear()
            for i in fd:
                i = i.replace('/', '\\')
                self.m_main_listBox.Append(i)

                self.ffmpg_wrp.file_list.append(i)
            
                path_dir = i.rsplit('\\', 1)[0]
                result = True # file exist..
                self.ffmpg_wrp.move_file_list.append(self.insert(i, '\\done', len(path_dir)))
            
                output_file = self.insert(i, '\\conv', len(path_dir))
                output_file = (output_file.rsplit('.', 1)[0] + '.' + "mp4")
                self.ffmpg_wrp.output_file_list.append(output_file)
                
            self.ffmpg_wrp.current_processed_file_number = 0                       
            self.status = ST_LIST_CHANGED
            self.prepare_ready_to_encode_interface()
        return result


    def insert(self, source_str, insert_str, pos):
        return source_str[:pos]+insert_str+source_str[pos:]


    def choose_dir(self, event):
        '''
        Searches all files in the directory, generates a list of incoming, converted and moved files
        '''

        self.m_main_listBox.Clear()
        
        
        result = False
        path_dir = ''
        dlg = wx.DirDialog(self, message="Choose a folder")
        if dlg.ShowModal() == wx.ID_OK:
            path_dir = dlg.GetPath()
        dlg.Destroy()
                
        if path_dir:
           path_dir = str(path_dir)
        else:
            return False
        path_dir = path_dir.replace('/', '\\')
        if not path_dir:
            return False
        else:
            os.chdir(path_dir)
        for root, dirs, files in os.walk(path_dir, topdown = False):
            for name in files:
                temp_str = os.path.join(root, name)
                if '\\conv\\' in temp_str or '\\done\\' in temp_str or \
                        'NULL' in temp_str or 'ffmpeg2pass' in temp_str:
                    continue
                extent = temp_str.rsplit('.',1)[1]
                if extent not in ('mp4', 'avi', 'flv', 'mkv', 'mov', 'wmv', 'asf', 'm4v', 'mpg', 'mpeg'):
                    continue
                self.ffmpg_wrp.file_list.append(temp_str)
                result = True # file exist..
                self.ffmpg_wrp.move_file_list.append(self.insert(temp_str, '\\done', len(path_dir)))
            
                output_file = self.insert(temp_str, '\\conv', len(path_dir))
                output_file = (output_file.rsplit('.', 1)[0] + '.' + "mp4")
                self.ffmpg_wrp.output_file_list.append(output_file)

        for name in self.ffmpg_wrp.file_list:
            print(name)
            self.m_main_listBox.Append(name)
  
        if result: 
            self.prepare_ready_to_encode_interface()
            self.ffmpg_wrp.current_processed_file_number = 0
        return result


    def on_run(self, event):
        '''
        main working function
        '''
        if not os.path.exists(self.settings.ffmpeg_location):
            wx.MessageBox('It isn\'t possible to locate ffmpeg.exe. Please set path to ffmpeg.exe in settings', 'ffmpeg location problem', wx.OK)
            return
   
     
        
        self.prepare_encoding_interface()


        self.ffmpg_wrp.set_keep_aspect(self.m_checkBox_keep_ratio.Get3StateValue())
        self.ffmpg_wrp.set_keep_resolution(self.m_checkBox_keep_resolution.Get3StateValue())
        self.ffmpg_wrp.set_bitrate(self.bitrate.GetValue())
        self.ffmpg_wrp.set_resX(self.res_x.GetValue())
        self.ffmpg_wrp.set_resY(self.res_y.GetValue())

        
        self.timer.Start(self.timer_period)

        self.conv_thread = threading.Thread(target = self.ffmpg_wrp.converting_thread)
        self.status = ST_ENCODING
        self.conv_thread.start()


    def on_pause(self, event):
        
        if self.status == ST_PAUSED:
            psProcess = psutil.Process(pid=self.process.pid)
            psProcess.resume()
            self.status = self.before_pause_status
            self.timer.Start()
            self.m_bt_pause.SetLabel('Pause')
            self.menuitem_pause.SetItemLabel('Pause\tCtrl+P')
        else:
            self.before_pause_status = self.status
            self.status = ST_PAUSED
            psProcess = psutil.Process(pid=self.process.pid)
            psProcess.suspend()
            self.timer.Stop()
            self.m_bt_pause.SetLabel('Continue')
            self.menuitem_pause.SetItemLabel('Continue\tCtrl+P')
           

    def on_stop(self, event):
        if (not self.process == None) and (self.process.poll() == None):
            psProcess = psutil.Process(pid = self.process.pid)
            psProcess.kill() 
        #print(str(self.conv_thread.is_alive()))
        #time.sleep(3)
        #print(str(self.conv_thread.is_alive()))
        self.m_statusBar2.SetStatusText('   Encoding stopped.')
        self.m_gauge1.SetValue(0)
        self.m_staticText7.SetLabel('')
        self.m_staticText_timetoend.SetLabel('')
        if self.ffmpg_wrp.current_processed_file_number < len(self.ffmpg_wrp.file_list):
            self.status = ST_STOPPED
            self.prepare_ready_to_encode_interface()
        else:
            self.status = ST_WAITING
            self.prepare_waiting_interface()

        self.timer.Stop()


    def on_closing(self, event): 
        self.status = ST_STOPPED
        self.timer.Stop()
        if (not self.process == None) and (self.process.poll() == None):
            psProcess = psutil.Process(pid = self.process.pid)
            psProcess.kill()         
        self.settings.res_x = self.res_x.GetValue()
        self.settings.res_y = self.res_y.GetValue()
        self.settings.bitrate = self.bitrate.GetValue() 
        self.settings.write_settings()

        os._exit(1)

    def on_check_keep_resolution( self, event ):
        event.Skip()

    def on_check_keep_aspect( self, event ):
        event.Skip()




if __name__ == "__main__":
    app = wx.App()
    frame = SimpleVideoEncoder(None)
    frame.Show()
    app.MainLoop()
    


 
