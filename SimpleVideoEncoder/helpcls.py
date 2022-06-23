import wx 


class Help ( wx.Frame ):

    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"Help", pos = wx.DefaultPosition, size = wx.Size( 500,300 ), style = wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN | wx.TAB_TRAVERSAL )

        self.SetSizeHints( wx.Size( 500,300 ), wx.DefaultSize )

        bSizer10 = wx.BoxSizer( wx.VERTICAL )

        icon = wx.Icon()
        icon.CopyFromBitmap(wx.Bitmap("vico.ico", wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)

        self.m_htmlWin1 = wx.html.HtmlWindow( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 300,200 ), wx.html.HW_SCROLLBAR_AUTO )
        self.m_htmlWin1.SetMinSize( wx.Size( 300,200 ) )
        self.m_htmlWin1.LoadPage('VC_help_en.html')

        bSizer10.Add( self.m_htmlWin1, 1, wx.ALL|wx.EXPAND, 1 )


        self.SetSizer( bSizer10 )
        self.Layout()

        self.Centre( wx.BOTH )

    def __del__( self ):
        pass
