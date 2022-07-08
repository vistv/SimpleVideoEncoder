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

    DATA_FILE_NAME = path.expandvars(r'%APPDATA%\SimpleVideoEncoder\persistent_data.pickle')        
    DATA_FILE_PATH = DATA_FILE_NAME.rsplit('\\', 1)[0] + '\\'
        

    settings = Settings(DATA_FILE_NAME)
        
    helpframe = None
    aboutframe = None
    timer_period = 200 #ms
    
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
        self.m_checkBox_keep_ratio.Set3StateValue(self.settings.is_keep_ratio)
        self.m_checkBox_keep_resolution.Set3StateValue(self.settings.is_keep_resolution)
        self.on_check_keep_ratio(1)
        self.on_check_keep_resolution(1)

        if self.settings.bitrate_choise == 0:
            self.m_radioBtn_lbtrt.SetValue(1)
            self.bitrate.Disable()
        elif self.settings.bitrate_choise == 1:
            self.m_radioBtn_mbtrt.SetValue(1)
            self.bitrate.Disable()
        elif self.settings.bitrate_choise == 2:
            self.m_radioBtn_hbtrt.SetValue(1)
            self.bitrate.Disable()
        else:
            self.m_radioBtn_obtrt.SetValue(1)
            self.bitrate.Enable()

        self.prepare_waiting_interface()

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_timer, self.timer)


    def build_ui(self, parent):
  
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = 'Simple video encoder', pos = wx.DefaultPosition, size = wx.Size( 700,520 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )
        
        self.SetSizeHints( wx.Size( 700,520 ), wx.DefaultSize )
        
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

        self.Bind(wx.EVT_MENU, self.on_encode, self.menuitem_encode)
        self.Bind(wx.EVT_MENU, self.on_pause, self.menuitem_pause)
        self.Bind(wx.EVT_MENU, self.on_stop, self.menuitem_stop)

        self.Bind(wx.EVT_MENU, self.on_help, self.menuitem_help)
        self.Bind(wx.EVT_MENU, self.on_about, self.menuitem_about)
        
 ##########################################################################            
        
        bSizer7 = wx.BoxSizer( wx.VERTICAL )

        self.m_panel4 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer18 = wx.BoxSizer( wx.VERTICAL )

        bSizer9 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer14 = wx.BoxSizer( wx.VERTICAL )

        sbSizer3 = wx.StaticBoxSizer( wx.StaticBox( self.m_panel4, wx.ID_ANY, wx.EmptyString ), wx.VERTICAL )

        self.bt_dir = wx.Button( sbSizer3.GetStaticBox(), wx.ID_ANY, u"Open Directory", wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer3.Add( self.bt_dir, 1, wx.ALL|wx.EXPAND, 5 )

        self.bt_input = wx.Button( sbSizer3.GetStaticBox(), wx.ID_ANY, u" Open file(s)   ", wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer3.Add( self.bt_input, 1, wx.ALL|wx.EXPAND, 5 )


        bSizer14.Add( sbSizer3, 1, wx.EXPAND, 5 )


        bSizer9.Add( bSizer14, 1, wx.EXPAND, 0 )

        sbSizer1 = wx.StaticBoxSizer( wx.StaticBox( self.m_panel4, wx.ID_ANY, u"Resolution" ), wx.VERTICAL )

        self.m_checkBox_keep_resolution = wx.CheckBox( sbSizer1.GetStaticBox(), wx.ID_ANY, u"Keep resolution", wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer1.Add( self.m_checkBox_keep_resolution, 0, wx.ALL, 5 )

        self.m_checkBox_keep_ratio = wx.CheckBox( sbSizer1.GetStaticBox(), wx.ID_ANY, u"Keep aspect ratio", wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer1.Add( self.m_checkBox_keep_ratio, 0, wx.ALL, 5 )

        bSizer21 = wx.BoxSizer( wx.VERTICAL )

        bSizer22 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText9 = wx.StaticText( sbSizer1.GetStaticBox(), wx.ID_ANY, u"Resolution X:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText9.Wrap( -1 )

        bSizer22.Add( self.m_staticText9, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

        self.res_x = wx.TextCtrl( sbSizer1.GetStaticBox(), wx.ID_ANY, u"854", wx.DefaultPosition, wx.Size( 50,-1 ), wx.TE_CENTER )
        bSizer22.Add( self.res_x, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


        bSizer21.Add( bSizer22, 1, wx.EXPAND, 5 )

        bSizer24 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText11 = wx.StaticText( sbSizer1.GetStaticBox(), wx.ID_ANY, u"Resolution Y:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText11.Wrap( -1 )

        bSizer24.Add( self.m_staticText11, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

        self.res_y = wx.TextCtrl( sbSizer1.GetStaticBox(), wx.ID_ANY, u"480", wx.DefaultPosition, wx.Size( 50,-1 ), wx.TE_CENTER )
        bSizer24.Add( self.res_y, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


        bSizer21.Add( bSizer24, 1, wx.EXPAND, 5 )


        sbSizer1.Add( bSizer21, 1, wx.EXPAND, 5 )


        bSizer9.Add( sbSizer1, 2, wx.EXPAND, 5 )

        sbSizer2 = wx.StaticBoxSizer( wx.StaticBox( self.m_panel4, wx.ID_ANY, u"Bitrate" ), wx.VERTICAL )

        self.m_radioBtn_lbtrt = wx.RadioButton( sbSizer2.GetStaticBox(), wx.ID_ANY, u"Low bitrate", wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer2.Add( self.m_radioBtn_lbtrt, 0, wx.ALL, 5 )

        self.m_radioBtn_mbtrt = wx.RadioButton( sbSizer2.GetStaticBox(), wx.ID_ANY, u"Middle bitrate", wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer2.Add( self.m_radioBtn_mbtrt, 0, wx.ALL, 5 )

        self.m_radioBtn_hbtrt = wx.RadioButton( sbSizer2.GetStaticBox(), wx.ID_ANY, u"High bitrate", wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer2.Add( self.m_radioBtn_hbtrt, 0, wx.ALL, 5 )

        bSizer16 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_radioBtn_obtrt = wx.RadioButton( sbSizer2.GetStaticBox(), wx.ID_ANY, u"Own bitrate (kBps)", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer16.Add( self.m_radioBtn_obtrt, 0, wx.ALL, 5 )

        self.bitrate = wx.TextCtrl( sbSizer2.GetStaticBox(), wx.ID_ANY, u"1000", wx.DefaultPosition, wx.Size( 50,-1 ), wx.TE_CENTER )
        bSizer16.Add( self.bitrate, 0, wx.ALL, 5 )


        sbSizer2.Add( bSizer16, 1, wx.EXPAND, 5 )


        bSizer9.Add( sbSizer2, 2, wx.EXPAND, 5 )

        bSizer20 = wx.BoxSizer( wx.VERTICAL )

        sbSizer4 = wx.StaticBoxSizer( wx.StaticBox( self.m_panel4, wx.ID_ANY, wx.EmptyString ), wx.VERTICAL )

        self.setting_butt = wx.Button( sbSizer4.GetStaticBox(), wx.ID_ANY, u"Setting", wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer4.Add( self.setting_butt, 1, wx.ALL|wx.EXPAND, 5 )

        self.m_button_help = wx.Button( sbSizer4.GetStaticBox(), wx.ID_ANY, u"Help", wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer4.Add( self.m_button_help, 1, wx.ALL|wx.EXPAND, 5 )


        bSizer20.Add( sbSizer4, 1, wx.EXPAND, 5 )


        bSizer9.Add( bSizer20, 1, wx.EXPAND, 5 )

        sbSizer5 = wx.StaticBoxSizer( wx.StaticBox( self.m_panel4, wx.ID_ANY, wx.EmptyString ), wx.VERTICAL )

        self.bt_encode = wx.Button( sbSizer5.GetStaticBox(), wx.ID_ANY, u"CONVERT", wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer5.Add( self.bt_encode, 1, wx.ALL|wx.EXPAND, 5 )


        bSizer9.Add( sbSizer5, 1, wx.EXPAND, 5 )


        bSizer18.Add( bSizer9, 1, wx.EXPAND, 5 )


        self.m_panel4.SetSizer( bSizer18 )
        self.m_panel4.Layout()
        bSizer18.Fit( self.m_panel4 )
        bSizer7.Add( self.m_panel4, 2, wx.EXPAND|wx.TOP|wx.RIGHT|wx.LEFT, 1 )

        bSizer12 = wx.BoxSizer( wx.HORIZONTAL )

        m_main_listBoxChoices = []
        self.m_main_listBox = wx.ListBox( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,-1 ), m_main_listBoxChoices, 0 )
        bSizer12.Add( self.m_main_listBox, 6, wx.ALL|wx.EXPAND, 0 )

        self.m_panel3 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer13 = wx.BoxSizer( wx.VERTICAL )

        self.m_button_up = wx.Button( self.m_panel3, wx.ID_ANY, u"Up", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer13.Add( self.m_button_up, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

        self.m_button_down = wx.Button( self.m_panel3, wx.ID_ANY, u"Down", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer13.Add( self.m_button_down, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

        self.m_button_del = wx.Button( self.m_panel3, wx.ID_ANY, u"Del", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer13.Add( self.m_button_del, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )

        self.m_button_add = wx.Button( self.m_panel3, wx.ID_ANY, u"Add", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer13.Add( self.m_button_add, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )


        self.m_panel3.SetSizer( bSizer13 )
        self.m_panel3.Layout()
        bSizer13.Fit( self.m_panel3 )
        bSizer12.Add( self.m_panel3, 1, wx.EXPAND |wx.ALL, 1 )


        bSizer7.Add( bSizer12, 5, wx.EXPAND, 5 )

        self.m_panel2 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer91 = wx.BoxSizer( wx.VERTICAL )

        gSizer2 = wx.GridSizer( 0, 2, 0, 0 )

        self.m_staticText7 = wx.StaticText( self.m_panel2, wx.ID_ANY, u"Encoding progress:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText7.Wrap( -1 )

        gSizer2.Add( self.m_staticText7, 0, wx.ALL, 5 )

        self.m_staticText_timetoend = wx.StaticText( self.m_panel2, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText_timetoend.Wrap( -1 )

        gSizer2.Add( self.m_staticText_timetoend, 0, wx.ALL, 5 )


        bSizer91.Add( gSizer2, 1, wx.EXPAND, 5 )

        bSizer11 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_gauge1 = wx.Gauge( self.m_panel2, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
        self.m_gauge1.SetValue( 0 )
        bSizer11.Add( self.m_gauge1, 1, wx.ALL|wx.EXPAND, 5 )

        self.m_bt_pause = wx.Button( self.m_panel2, wx.ID_ANY, u"Pause", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer11.Add( self.m_bt_pause, 0, wx.ALL|wx.EXPAND, 5 )

        self.m_bt_stop = wx.Button( self.m_panel2, wx.ID_ANY, u"Stop", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer11.Add( self.m_bt_stop, 0, wx.ALL|wx.EXPAND, 5 )


        bSizer91.Add( bSizer11, 1, wx.EXPAND, 5 )


        self.m_panel2.SetSizer( bSizer91 )
        self.m_panel2.Layout()
        bSizer91.Fit( self.m_panel2 )
        bSizer7.Add( self.m_panel2, 1, wx.EXPAND |wx.ALL, 0 )

###########################################################################
        self.SetSizer( bSizer7 )
        self.Layout()

        self.Centre( wx.BOTH )


    def connect_events(self):
        self.bt_dir.Bind( wx.EVT_BUTTON, self.choose_dir )
        self.bt_input.Bind( wx.EVT_BUTTON, self.choose_files )
        self.setting_butt.Bind( wx.EVT_BUTTON, self.setting_dialog )
        self.m_button_help.Bind(wx.EVT_BUTTON, self.on_help)
        self.bt_encode.Bind( wx.EVT_BUTTON, self.on_encode )
        self.Bind( wx.EVT_CLOSE, self.on_closing )
        self.m_bt_pause.Bind( wx.EVT_BUTTON, self.on_pause )
        self.m_bt_stop.Bind( wx.EVT_BUTTON, self.on_stop )
        self.Bind(self.ffmpg_wrp.EVT_ENC_END_EVENT, self.on_enc_end)
        self.Bind(self.ffmpg_wrp.EVT_FILE_END_EVENT, self.on_file_enc)
        self.m_checkBox_keep_resolution.Bind( wx.EVT_CHECKBOX, self.on_check_keep_resolution )
        self.m_checkBox_keep_ratio.Bind( wx.EVT_CHECKBOX, self.on_check_keep_ratio )
        self.m_radioBtn_lbtrt.Bind( wx.EVT_RADIOBUTTON, self.on_rbutton_low )
        self.m_radioBtn_mbtrt.Bind( wx.EVT_RADIOBUTTON, self.on_rbutton_mid )
        self.m_radioBtn_hbtrt.Bind( wx.EVT_RADIOBUTTON, self.on_rbutton_high )
        self.m_radioBtn_obtrt.Bind( wx.EVT_RADIOBUTTON, self.on_rbutton_own )
        self.m_button_up.Bind( wx.EVT_BUTTON, self.on_button_up )
        self.m_button_down.Bind( wx.EVT_BUTTON, self.on_button_down )
        self.m_button_del.Bind( wx.EVT_BUTTON, self.on_button_del )
        self.m_button_add.Bind( wx.EVT_BUTTON, self.on_button_add )

  
    def prepare_waiting_interface(self):
        self.bt_input.Enable()
        self.bt_dir.Enable()
        self.bt_encode.Disable()
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

        self.m_button_up.Enable()
        self.m_button_down.Enable()
        self.m_button_del.Enable()
        self.m_button_add.Enable()


    def prepare_ready_to_encode_interface(self):
        self.bt_input.Enable()
        self.bt_dir.Enable()
        self.bt_encode.Enable()
        self.setting_butt.Enable()

        self.m_bt_pause.Disable()
        self.m_bt_stop.Disable()

        self.m_button_up.Enable()
        self.m_button_down.Enable()
        self.m_button_del.Enable()
        self.m_button_add.Enable()

        self.menuitem_openfile.Enable(enable = True)
        self.menuitem_opendirectory.Enable(enable = True)
        self.menuitem_encode.Enable(enable = True)
        self.menuitem_pause.Enable(enable = False)
        self.menuitem_stop.Enable(enable = False)


    def prepare_encoding_interface(self):
        self.bt_input.Disable()
        self.bt_dir.Disable()
        self.bt_encode.Disable()
        self.setting_butt.Disable()

        self.m_bt_pause.Enable()
        self.m_bt_stop.Enable()

        self.menuitem_openfile.Enable(enable = False)
        self.menuitem_opendirectory.Enable(enable = False)
        self.menuitem_encode.Enable(enable = False)
        self.menuitem_pause.Enable(enable = True)
        self.menuitem_stop.Enable(enable = True)

        self.m_button_up.Enable()
        self.m_button_down.Enable()
        self.m_button_del.Enable()
        self.m_button_add.Enable()

        
    def on_enc_end(self, event):
        self.prepare_waiting_interface()


    def update_timer(self, event):
 
        try:
            full_duration = self.ffmpg_wrp.movie_duration[self.ffmpg_wrp.current_processed_file_number]
        except:
            if self.ffmpg_wrp.status == ST_FINISHED:
                self.m_statusBar2.SetStatusText('   Everything is already done!')
            if self.ffmpg_wrp.status <= ST_WAITING:
                self.m_statusBar2.SetStatusText('   Waiting')
            if self.ffmpg_wrp.status >= ST_ENCODING:
                self.m_statusBar2.SetStatusText('   Starting...')
            if self.ffmpg_wrp.status == ST_STOPPED:
                self.m_statusBar2.SetStatusText('   Encoding was stopped.')
            
            self.m_staticText_timetoend.SetLabel('')
            return

        self.m_staticText7.SetLabel(self.ffmpg_wrp.text_status)

        if (not self.ffmpg_wrp.queue.empty()) and self.ffmpg_wrp.status >= ST_ENCODING:
            line = str(self.ffmpg_wrp.queue.get())

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
                    if self.ffmpg_wrp.status == ST_1PASS:
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
   

    def choose_files(self, event, is_appending = False):
        '''
            dialog to choose files
        '''
        result = False
   
        fd = None
        dialog = wx.FileDialog(self, "Choose a file", wildcard="Video files | .3g2; *.3gp; *.3gp2; *.3gpp; *.3gpp2; *.asf; *.asx; *.avi; *.bin; *.dat; *.drv; *.f4v; *.flv; *.gtp; *.h264; *.m4v; *.mkv; *.mod; *.moov; *.mov; *.mp4; *.mpeg; *.mpg; *.mts; *.rm; *.rmvb; *.spl; *.srt; *.stl; *.swf; *.ts; *.vcd; *.vid; *.vid; *.vid; *.vob; *.webm; *.wm; *.wmv; *.yuv", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE)
        if dialog.ShowModal() == wx.ID_OK:
            fd = dialog.GetPaths()
        
        if fd:
            if not is_appending:
                self.m_main_listBox.Clear()
                self.ffmpg_wrp.clear_movies_data()

            for i in fd:
                i = i.replace('/', '\\')
                
                if self.m_main_listBox.FindString(i) > -1: continue

                self.m_main_listBox.Append(i)

                self.ffmpg_wrp.file_list.append(i)
            
                path_dir = i.rsplit('\\', 1)[0]
                result = True # file exist..
                self.ffmpg_wrp.move_file_list.append(self.insert(i, '\\done', len(path_dir)))
            
                output_file = self.insert(i, '\\conv', len(path_dir))
                output_file = (output_file.rsplit('.', 1)[0] + '.' + "mp4")
                self.ffmpg_wrp.output_file_list.append(output_file)

            self.prepare_ready_to_encode_interface()
        return result


    def insert(self, source_str, insert_str, pos):
        return source_str[:pos]+insert_str+source_str[pos:]


    def choose_dir(self, event):
        '''
        Searches all files in the directory, generates a list of incoming, converted and moved files
        '''

        self.m_main_listBox.Clear()
        self.ffmpg_wrp.clear_movies_data()
        
        
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
            self.m_main_listBox.Append(name)
  
        if result: 
            self.prepare_ready_to_encode_interface()

        return result


    def on_encode(self, event):
        '''
        main working function
        '''
        if not os.path.exists(self.settings.ffmpeg_location):
            wx.MessageBox('It isn\'t possible to locate ffmpeg.exe. Please set path to ffmpeg.exe in settings', 'ffmpeg location problem', wx.OK)
            return
   
     
        
        self.prepare_encoding_interface()


        self.ffmpg_wrp.set_keep_ratio(self.m_checkBox_keep_ratio.Get3StateValue())
        self.ffmpg_wrp.set_keep_resolution(self.m_checkBox_keep_resolution.Get3StateValue())
        self.ffmpg_wrp.set_bitrate(self.bitrate.GetValue())
        self.ffmpg_wrp.set_resX(self.res_x.GetValue())
        self.ffmpg_wrp.set_resY(self.res_y.GetValue())
        self.ffmpg_wrp.set_is_upscale_forbidden(self.settings.is_upscale_forbidden)
        self.ffmpg_wrp.set_bitrate_choise(self.settings.bitrate_choise)
        self.ffmpg_wrp.set_ffmpeg_location(self.settings.ffmpeg_location)
        self.ffmpg_wrp.set_limit_size_mb(self.settings.limit_size_mb)
        self.ffmpg_wrp.set_timer_period(self.timer_period)
        self.ffmpg_wrp.set_DATA_FILE_PATH(self.DATA_FILE_PATH)
        self.ffmpg_wrp.set_own_encode_param(self.settings.own_encode_param)
        self.ffmpg_wrp.set_is_use_own_encode_param(self.settings.is_use_own_encode_param)
        self.ffmpg_wrp.set_default_encode_param(self.settings.default_encode_param)
        self.ffmpg_wrp.set_is_two_pass(self.settings.is_two_pass)
        self.ffmpg_wrp.set_is_cryterium_on(self.settings.is_cryterium_on)

        
        self.timer.Start(self.timer_period)

        self.conv_thread = threading.Thread(target = self.ffmpg_wrp.converting_thread)
        self.ffmpg_wrp.status = ST_ENCODING
        self.conv_thread.start()


    def on_pause(self, event):
        
        if self.ffmpg_wrp.status == ST_PAUSED:
            psProcess = psutil.Process(pid=self.ffmpg_wrp.process.pid)
            psProcess.resume()
            self.ffmpg_wrp.status = self.before_pause_status
            self.timer.Start()
            self.m_bt_pause.SetLabel('Pause')
            self.menuitem_pause.SetItemLabel('Pause\tCtrl+P')
        else:
            self.before_pause_status = self.ffmpg_wrp.status
            self.ffmpg_wrp.status = ST_PAUSED
            psProcess = psutil.Process(pid=self.ffmpg_wrp.process.pid)
            psProcess.suspend()
            self.timer.Stop()
            self.m_bt_pause.SetLabel('Continue')
            self.menuitem_pause.SetItemLabel('Continue\tCtrl+P')
           

    def on_stop(self, event):
        if (not self.ffmpg_wrp.process == None) and (self.ffmpg_wrp.process.poll() == None):
            psProcess = psutil.Process(pid = self.ffmpg_wrp.process.pid)
            psProcess.kill() 
        #print(str(self.conv_thread.is_alive()))
        #time.sleep(3)
        #print(str(self.conv_thread.is_alive()))
        self.m_statusBar2.SetStatusText('   Encoding stopped.')
        self.m_gauge1.SetValue(0)
        self.m_staticText7.SetLabel('')
        self.m_staticText_timetoend.SetLabel('')
        self.ffmpg_wrp.set_text_status('')
        if self.ffmpg_wrp.current_processed_file_number < len(self.ffmpg_wrp.file_list):
            self.ffmpg_wrp.status = ST_STOPPED
            self.prepare_ready_to_encode_interface()
        else:
            self.ffmpg_wrp.status = ST_WAITING
            self.prepare_waiting_interface()

        self.timer.Stop()


    def on_closing(self, event): 
        self.ffmpg_wrp.status = ST_STOPPED
        self.timer.Stop()
        if (not self.ffmpg_wrp.process == None) and (self.ffmpg_wrp.process.poll() == None):
            psProcess = psutil.Process(pid = self.ffmpg_wrp.process.pid)
            psProcess.kill()         
        self.settings.res_x = self.res_x.GetValue()
        self.settings.res_y = self.res_y.GetValue()
        self.settings.bitrate = self.bitrate.GetValue() 
        self.settings.is_keep_ratio =  self.m_checkBox_keep_ratio.Get3StateValue()
        self.settings.is_keep_resolution =  self.m_checkBox_keep_resolution.Get3StateValue()

        if self.m_radioBtn_lbtrt.GetValue():
            self.settings.bitrate_choise = 0
        elif self.m_radioBtn_mbtrt.GetValue():
            self.settings.bitrate_choise = 1
        elif self.m_radioBtn_hbtrt.GetValue():
            self.settings.bitrate_choise = 2
        else:
            self.settings.bitrate_choise = 3

        self.settings.write_settings()

        os._exit(1)


    def on_check_keep_resolution( self, event ):
        if self.m_checkBox_keep_resolution.Get3StateValue():
            self.res_x.Disable()
            self.res_y.Disable()
            self.m_checkBox_keep_ratio.Disable()
            
        else:
            self.res_x.Enable()
            self.m_checkBox_keep_ratio.Enable()
            if not self.m_checkBox_keep_ratio.Get3StateValue():
                self.res_y.Enable()
            

    def on_check_keep_ratio( self, event ):
        if self.m_checkBox_keep_ratio.Get3StateValue():
            self.res_y.Disable()
        else:
            if not self.m_checkBox_keep_resolution.Get3StateValue():
                self.res_y.Enable()


    def on_rbutton_low( self, event ):
        self.settings.bitrate_choise = 0
        self.bitrate.Disable()


    def on_rbutton_mid( self, event ):
        self.settings.bitrate_choise = 1
        self.bitrate.Disable()


    def on_rbutton_high( self, event ):
        self.settings.bitrate_choise = 2
        self.bitrate.Disable()


    def on_rbutton_own( self, event ):
        self.settings.bitrate_choise = 3
        self.bitrate.Enable()

    def on_button_up( self, event ):
        sel_num = self.m_main_listBox.GetSelection()
        if (sel_num > self.ffmpg_wrp.current_processed_file_number) and sel_num > 0:
            sel_val = self.m_main_listBox.GetString(sel_num)
            self.m_main_listBox.Delete(sel_num)
            self.m_main_listBox.Insert(sel_val, sel_num  - 1)
            self.m_main_listBox.SetSelection(sel_num  - 1)
            
            file = self.ffmpg_wrp.file_list[sel_num]
            self.ffmpg_wrp.file_list.remove(file)
            self.ffmpg_wrp.file_list.insert(sel_num  - 1, file)

            file = self.ffmpg_wrp.output_file_list[sel_num]
            self.ffmpg_wrp.output_file_list.remove(file)
            self.ffmpg_wrp.output_file_list.insert(sel_num  - 1, file)

            file = self.ffmpg_wrp.move_file_list[sel_num]
            self.ffmpg_wrp.move_file_list.remove(file)
            self.ffmpg_wrp.move_file_list.insert(sel_num  - 1, file)
            

    def on_button_down( self, event ):
        sel_num = self.m_main_listBox.GetSelection()
        count = self.m_main_listBox.GetCount()
        if (sel_num >= self.ffmpg_wrp.current_processed_file_number) and sel_num < (count - 1):
            sel_val = self.m_main_listBox.GetString(sel_num)
            self.m_main_listBox.Delete(sel_num)
            self.m_main_listBox.Insert(sel_val, sel_num  + 1)
            self.m_main_listBox.SetSelection(sel_num  + 1)
            
            file = self.ffmpg_wrp.file_list[sel_num]
            self.ffmpg_wrp.file_list.remove(file)
            self.ffmpg_wrp.file_list.insert(sel_num  + 1, file)

            file = self.ffmpg_wrp.output_file_list[sel_num]
            self.ffmpg_wrp.output_file_list.remove(file)
            self.ffmpg_wrp.output_file_list.insert(sel_num  + 1, file)

            file = self.ffmpg_wrp.move_file_list[sel_num]
            self.ffmpg_wrp.move_file_list.remove(file)
            self.ffmpg_wrp.move_file_list.insert(sel_num  + 1, file)


    def on_button_del( self, event ):
        sel_num = self.m_main_listBox.GetSelection()
        
        if sel_num > -1:
            
            self.m_main_listBox.Delete(sel_num)

            file = self.ffmpg_wrp.file_list[sel_num]
            self.ffmpg_wrp.file_list.remove(file)

            file = self.ffmpg_wrp.output_file_list[sel_num]
            self.ffmpg_wrp.output_file_list.remove(file)

            file = self.ffmpg_wrp.move_file_list[sel_num]
            self.ffmpg_wrp.move_file_list.remove(file)


    def on_button_add( self, event ):
        self.choose_files(event, is_appending = True)


    def on_file_enc(self, event):
        if self.ffmpg_wrp.last_enc_result == '':
            self.m_main_listBox.SetSelection(-1)
            return

        if self.ffmpg_wrp.last_enc_result == 'next':
            self.m_main_listBox.SetSelection(self.ffmpg_wrp.current_processed_file_number)
            return
                
        self.m_main_listBox.SetString(self.ffmpg_wrp.processed_file_number, self.m_main_listBox.GetString(self.ffmpg_wrp.processed_file_number) + self.ffmpg_wrp.last_enc_result)






if __name__ == "__main__":
    app = wx.App()
    frame = SimpleVideoEncoder(None)
    frame.Show()
    app.MainLoop()
    


 
