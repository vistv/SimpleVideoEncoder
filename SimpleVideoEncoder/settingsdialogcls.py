import wx 


class SettingsDialog (wx.Dialog):


    def __init__( self, parent):
        
        self.settings = parent.settings



        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Settings", pos = wx.DefaultPosition, size = wx.DefaultSize, style = wx.DEFAULT_DIALOG_STYLE )

        self.SetSizeHints( wx.Size( -1,-1 ), wx.DefaultSize )

        bSizer3 = wx.BoxSizer( wx.VERTICAL )

        self.m_staticText5 = wx.StaticText( self, wx.ID_ANY, u"ffmpeg location:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText5.Wrap( -1 )

        bSizer3.Add( self.m_staticText5, 0, wx.ALL, 5 )

        bSizer4 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_ffmpegpath_textCtrl = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 300,-1 ), 0 )
        self.m_ffmpegpath_textCtrl.SetMinSize( wx.Size( 300,-1 ) )

        bSizer4.Add( self.m_ffmpegpath_textCtrl, 0, wx.ALL, 5 )

        self.m_button_findffmpeg = wx.Button( self, wx.ID_ANY, u"Find ffmpeg", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer4.Add( self.m_button_findffmpeg, 1, wx.ALL|wx.EXPAND, 5 )


        bSizer3.Add( bSizer4, 1, wx.EXPAND, 5 )

        self.m_staticline1 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
        bSizer3.Add( self.m_staticline1, 0, wx.EXPAND |wx.ALL, 5 )

        bSizer5 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText6 = wx.StaticText( self, wx.ID_ANY, u"Number of passes:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText6.Wrap( -1 )

        bSizer5.Add( self.m_staticText6, 1, wx.ALL|wx.EXPAND, 5 )

        self.m_radioBtn_1pass = wx.RadioButton( self, wx.ID_ANY, u"1 pass encoding", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer5.Add( self.m_radioBtn_1pass, 1, wx.ALL, 5 )

        self.m_radioBtn_2pass = wx.RadioButton( self, wx.ID_ANY, u"2 pass encoding", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer5.Add( self.m_radioBtn_2pass, 1, wx.ALL, 5 )


        bSizer3.Add( bSizer5, 1, wx.EXPAND, 5 )

        self.m_staticline3 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
        bSizer3.Add( self.m_staticline3, 0, wx.EXPAND |wx.ALL, 5 )

        bSizer7 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_check_conv_condit = wx.CheckBox( self, wx.ID_ANY, u"Encode only if size of 1 hour  is greater than (MB):", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_check_conv_condit.SetValue(True)
        bSizer7.Add( self.m_check_conv_condit, 0, wx.ALL|wx.EXPAND, 5 )

        self.m_textCtrl_cryterium = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer7.Add( self.m_textCtrl_cryterium, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


        bSizer3.Add( bSizer7, 1, wx.EXPAND, 5 )

        self.m_staticline4 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
        bSizer3.Add( self.m_staticline4, 0, wx.EXPAND |wx.ALL, 5 )

        bSizer8 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_Check_env_param = wx.CheckBox( self, wx.ID_ANY, u"Use own encoding parameters:", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer8.Add( self.m_Check_env_param, 0, wx.ALL|wx.EXPAND, 5 )

        self.m_textCtrl_encparam = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer8.Add( self.m_textCtrl_encparam, 1, wx.ALL, 5 )


        bSizer3.Add( bSizer8, 1, wx.EXPAND, 5 )

        self.m_staticline5 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
        bSizer3.Add( self.m_staticline5, 0, wx.EXPAND |wx.ALL, 5 )

        self.bSizer9 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_button_ok = wx.Button( self, wx.ID_OK, u"OK", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.bSizer9.Add( self.m_button_ok, 1, wx.ALL, 5 )

        self.m_button_cancel = wx.Button( self, wx.ID_CANCEL, u"Calcel", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.bSizer9.Add( self.m_button_cancel, 1, wx.ALL, 5 )


        bSizer3.Add( self.bSizer9, 1, wx.EXPAND, 5 )


        self.SetSizer( bSizer3 )
        self.Layout()
        bSizer3.Fit( self )

        self.Centre( wx.BOTH )

        self.m_button_ok.Bind(wx.EVT_BUTTON, self.onOK)
        self.m_check_conv_condit.Bind(wx.EVT_CHECKBOX, self.onCheck_conv_condit)
        self.m_Check_env_param.Bind(wx.EVT_CHECKBOX, self.onCheck_env_param)
        self.m_button_findffmpeg.Bind(wx.EVT_BUTTON, self.onFind_ffmpeg)


        self.settings.read_settings()
        self.init_ctls()


        self.m_textCtrl_cryterium.Enable(self.m_check_conv_condit.GetValue())
        self.m_textCtrl_encparam.Enable(self.m_Check_env_param.GetValue())


    def onFind_ffmpeg(self, event):
        fd = None
        dialog = wx.FileDialog(self, "ffmpeg.exe", wildcard='ffmpeg.exe | ffmpeg.exe', style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if dialog.ShowModal() == wx.ID_OK:
            fd = dialog.GetPaths()
            if fd[0]:
                self.m_ffmpegpath_textCtrl.SetValue(fd[0])


    def __del__( self ):
        self.settings.write_settings()


    def onCheck_conv_condit(self, event):
        self.m_textCtrl_cryterium.Enable(self.m_check_conv_condit.GetValue())
        self.m_textCtrl_encparam.Enable(self.m_Check_env_param.GetValue())


    def onCheck_env_param(self, event):
        self.m_textCtrl_cryterium.Enable(self.m_check_conv_condit.GetValue())
        self.m_textCtrl_encparam.Enable(self.m_Check_env_param.GetValue())


    def onOK(self, event):
        self.settings.ffmpeg_location = self.m_ffmpegpath_textCtrl.GetValue()
        self.settings.is_two_pass = self.m_radioBtn_2pass.GetValue()
        self.settings.is_cryterium_on = self.m_check_conv_condit.GetValue()
        self.settings.limit_size_mb = float(self.m_textCtrl_cryterium.GetValue())
        self.settings.is_use_own_encode_param = self.m_Check_env_param.GetValue()
        self.settings.own_encode_param = self.m_textCtrl_encparam.GetValue()
        
        self.settings.write_settings()
        self.EndModal(wx.ID_OK)


    def init_ctls(self):
        self.m_ffmpegpath_textCtrl.SetValue(self.settings.ffmpeg_location)
        self.m_radioBtn_2pass.SetValue(self.settings.is_two_pass)
        self.m_radioBtn_1pass.SetValue(not self.settings.is_two_pass)
        self.m_check_conv_condit.SetValue(self.settings.is_cryterium_on)
        self.m_textCtrl_cryterium.SetValue(str(self.settings.limit_size_mb)) 
        self.m_Check_env_param.SetValue(self.settings.is_use_own_encode_param)
        self.m_textCtrl_encparam.SetValue(self.settings.own_encode_param)


    def get_settings(self):
        return self.settings

