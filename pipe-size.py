Private Sub CommandButton3_Click()
'Dim DownFile As String, ctitle As String
'Savepath = GetFolder(ThisWorkbook.Path) + "\"

'Dim cht1 As Chart, ImageName As String, expt As Boolean
  frmMain.PrintForm

   'ImageName = ThisWorkbook.Path & "\frame1.jpg"
   ' expt = UserForm.Export(ImageName, "jpg")
End Sub

Private Sub CommandButton4_Click()
Dim vizzy As Boolean
vizzy = False
CommandButton1.Visible = vizzy: CommandButton2.Visible = vizzy: CommandButton3.Visible = vizzy
frmMain.PrintForm
vizzy = True
CommandButton1.Visible = vizzy: CommandButton2.Visible = vizzy: CommandButton3.Visible = vizzy
End Sub

Private Sub FramePlot_Click()

End Sub

Private Sub UserForm_Initialize()
 
Call cmdCalculate_Click
 
End Sub

Private Sub UserForm_Terminate()
 
 Dim cht1 As Chart, ImageName As String, expt As Boolean
  Set cht1 = Sheets("Plot").ChartObjects("PicPlott").Chart
   ImageName = ThisWorkbook.Path & "\temp1.jpg"
    If FileExists(ImageName) = False Then Kill ImageName
    End

 End Sub
 



Function GetFolder(strPath As String) As String

Dim fldr As FileDialog
Dim sItem As String
ChDir "C:\"
Set fldr = Application.FileDialog(msoFileDialogFolderPicker)
With fldr
    .Title = "Select Location of Counties Database"
    .AllowMultiSelect = False
    .InitialFileName = strPath
    If .Show <> -1 Then GoTo NextCode
    sItem = .SelectedItems(1)
End With
NextCode:
GetFolder = sItem
Set fldr = Nothing
End Function



Private Sub cmdCalculate_Click()
    Dim I As Integer
    Dim D0 As Single
    Dim theta As Single
    Dim HRadius As Single

   If sstResults.Value = 1 Then
      txtResult.Width = 50: txtResult2.Visible = True
    Else
    txtResult.Width = 100: txtResult2.Visible = False
    End If
    
    BDia = True
                DC = DrainageCoeff()
    Select Case sstResults.Value
    Case 0 '0~4: Drainage Area
        If optDInput0.Value = True Then
            TD = Val(txtInValue0.Text) / 12: S = Val(txtInValue1.Text) / 100:
            
           TD2 = Val(txtInValue0.Text): S2 = Val(txtInValue1.Text)
           Sheets("Plot").Range("Pipesize") = TD2: Sheets("Plot").Range("Slopes") = S2
           Call Plotlines(4, 1)
            
            TD = Val(txtInValue0.Text) / 12: S = Val(txtInValue1.Text) / 100:
            D0 = Val(txtSediment) * TD / 100
            theta = Arccos((TD - 2 * D0) / TD)
            HRadius = PipeArea(TD, D0, theta) / WP(TD, D0, theta)
            DA = 1.486 * PipeArea(TD, D0, theta) * HRadius ^ (2 / 3) * S ^ 0.5 / (9.64506173 * 10 ^ (-7) * Roughness(Val(txtInValue0)) * DC)
        qfz = 4
        End If
        
        If optDInput1.Value = True Then
               
            Q2 = Val(txtInValue0.Text)
            Sheets("Plot").Range("Discharge") = Q2
            Call Plotlines(2, 2)
            
            Q = Val(txtInValue0.Text)
            DA = QToArea(Q)
        End If
        If optDInput2.Value = True Then
            TD = Val(txtInValue0.Text) / 12: V = Val(txtInValue1.Text)
              
            TD2 = Val(txtInValue0.Text): V2 = Val(txtInValue1.Text)
            Sheets("Plot").Range("Pipesize") = TD2: Sheets("Plot").Range("Velocity") = V2
            Call Plotlines(4, 3)
            

            D0 = Val(txtSediment) * TD / 100
            theta = Arccos((TD - 2 * D0) / TD)
            HRadius = PipeArea(TD, D0, theta) / WP(TD, D0, theta)
            S = VToSlope(V, Roughness(Val(txtInValue0)), HRadius)
            DA = 1.486 / Roughness(Val(txtInValue0)) * PipeArea(TD, D0, theta) * HRadius ^ (2 / 3) * S ^ 0.5 / (9.64506173 * 10 ^ (-7) * DC)
        qfz = 4
        End If
        DA = DA / 43560 'Drainage area in acre
'        txtResult.Text = 10 * CLng(DA / 10 + 0.5)
        lblResult.Caption = "Drainage Area (acres)"
        txtResult.Text = Format(DA, "0.00")
    Case 1 '11~7: Tile Size
        If optDInput11.Value = True Then
            DA = Val(txtInValue3.Text) * 43560: S = Val(txtInValue2.Text) / 100
            Q = AreaToQ(DA)
             
            Q2 = Q: S2 = Val(txtInValue2.Text)
            Sheets("Plot").Range("Discharge") = Q2: Sheets("Plot").Range("Slopes") = S2
            Call Plotlines(2, 1)
            
            'TD = SecantMethod(0.1, 80) * 12 'Real tile dia in inch
            TD = DetD(Q)
        End If
        If optDInput9.Value = True Then
            Q = Val(txtInValue3.Text): S = Val(txtInValue2.Text) / 100
            
            Q2 = Val(txtInValue3.Text): S2 = Val(txtInValue2.Text)
            Sheets("Plot").Range("Discharge") = Q2: Sheets("Plot").Range("Slopes") = S2
            Call Plotlines(2, 1)
            
            TD = DetD(Q)
        End If
          lblResult.Caption = "Tile Size (inches)"
        If BDia = True Then
            txtResult.Text = PruductTile(TD)
            txtResult2.Text = Format(TD, "0.00")
        Else
            txtResult = ""
            
        End If
    Case 2 '17~13: Slope
        If optDInput17.Value = True Then
            DA = Val(txtInValue5.Text) * 43560: TD = Val(txtInValue4.Text) / 12
             
            DA2 = Val(txtInValue5.Text): TD2 = Val(txtInValue4.Text)
            Q2 = AreaToQ(DA)
            Sheets("Plot").Range("Discharge") = Q2: Sheets("Plot").Range("PipeSize") = TD2
            Call Plotlines(2, 4)
            
            D0 = Val(txtSediment) * TD / 100
            theta = Arccos((TD - 2 * D0) / TD)
            HRadius = PipeArea(TD, D0, theta) / WP(TD, D0, theta)
            S = (9.64506173 * 10 ^ (-7) * DA * DC * Roughness(Val(txtInValue4)) / (1.486 * PipeArea(TD, D0, theta) * HRadius ^ (2 / 3))) ^ 2
            S = S * 100
        End If
        If optDInput15.Value = True Then
            TD = Val(txtInValue5.Text) / 12: V = Val(txtInValue4.Text)
             
            V2 = Val(txtInValue4.Text): TD2 = Val(txtInValue5.Text)
            Sheets("Plot").Range("Velocity") = V2: Sheets("Plot").Range("PipeSize") = TD2
            Call Plotlines(3, 4)
            
            D0 = Val(txtSediment) * TD / 100
            theta = Arccos((TD - 2 * D0) / TD)
            HRadius = PipeArea(TD, D0, theta) / WP(TD, D0, theta)
            S = VToSlope(V, Roughness(Val(txtInValue5)), HRadius)
            S = S * 100
        End If
        If optDInput13.Value = True Then
            TD = Val(txtInValue5.Text) / 12: Q = Val(txtInValue4.Text)
              
            Q2 = Val(txtInValue4.Text): TD2 = Val(txtInValue5.Text)
            Sheets("Plot").Range("Discharge") = Q2: Sheets("Plot").Range("PipeSize") = TD2
            Call Plotlines(2, 4)
      
            D0 = Val(txtSediment) * TD / 100
            theta = Arccos((TD - 2 * D0) / TD)
            HRadius = PipeArea(TD, D0, theta) / WP(TD, D0, theta)
            S = (Q * Roughness(Val(txtInValue4)) / (1.486 * PipeArea(TD, D0, theta) * HRadius ^ (2 / 3))) ^ 2
            S = S * 100
        End If
                 lblResult.Caption = "Tile Slope (%)"
        txtResult.Text = Format(S, "0.00")
    Case 3 '23~19: Discharge
        If optDInput23.Value = True Then
            TD = Val(txtInValue7.Text) / 12: S = Val(txtInValue6.Text) / 100
               
            S2 = Val(txtInValue6.Text): TD2 = Val(txtInValue7.Text)
            Sheets("Plot").Range("Slopes") = S2: Sheets("Plot").Range("PipeSize") = TD2
            Call Plotlines(1, 4)
      
            D0 = Val(txtSediment) * TD / 100
            theta = Arccos((TD - 2 * D0) / TD)
            HRadius = PipeArea(TD, D0, theta) / WP(TD, D0, theta)
            Q = 1.486 * PipeArea(TD, D0, theta) * HRadius ^ (2 / 3) * S ^ 0.5 / Roughness(Val(txtInValue7))
        End If
        If optDInput22.Value = True Then
            DA = Val(txtInValue7.Text) * 43560 'drainage area in square feet
              
           DA2 = Val(txtInValue7.Text):  Q2 = AreaToQ(DA)
            Sheets("Plot").Range("Discharge") = Q2:
            Call Plotlines(2, 2)
      
            Q = AreaToQ(DA)
        End If
        If optDInput21.Value = True Then
            TD = Val(txtInValue7.Text) / 12: V = Val(txtInValue6.Text)
             
            V2 = Val(txtInValue6.Text): TD2 = Val(txtInValue7.Text)
            Sheets("Plot").Range("Velocity") = V2: Sheets("Plot").Range("PipeSize") = TD2
            Call Plotlines(3, 4)
            
            D0 = Val(txtSediment) * TD / 100
            theta = Arccos((TD - 2 * D0) / TD)
            Q = PipeArea(TD, D0, theta) * V
        End If
                 lblResult.Caption = "Flowrate (cfs)"
        txtResult.Text = Format(Q, "0.000")
    Case 4 '29~25: Velocity
        If optDInput29.Value = True Then
            TD = Val(txtInValue9.Text) / 12: S = Val(txtInValue8.Text) / 100
            
            TD2 = Val(txtInValue9.Text): S2 = Val(txtInValue8.Text)
            Sheets("Plot").Range("Pipesize") = TD2: Sheets("Plot").Range("Slopes") = S2
            Call Plotlines(4, 1)
          
            D0 = Val(txtSediment) * TD / 100
            theta = Arccos((TD - 2 * D0) / TD)
            HRadius = PipeArea(TD, D0, theta) / WP(TD, D0, theta)
            V = 1.486 / Roughness(Val(txtInValue9.Text)) * HRadius ^ (2 / 3) * S ^ 0.5
        End If
        If optDInput28.Value = True Then
            TD = Val(txtInValue9.Text) / 12: Q = Val(txtInValue8.Text)
              
            Q2 = Val(txtInValue8.Text): TD2 = Val(txtInValue9.Text)
            Sheets("Plot").Range("Discharge") = Q2: Sheets("Plot").Range("PipeSize") = TD2
            Call Plotlines(2, 4)
      
            D0 = Val(txtSediment) * TD / 100
            theta = Arccos((TD - 2 * D0) / TD)
            V = Q / PipeArea(TD, D0, theta)
        End If
        If optDInput27.Value = True Then
            TD = Val(txtInValue9.Text) / 12: DA = Val(txtInValue8.Text) * 43560
            
            DA2 = Val(txtInValue8.Text): TD2 = Val(txtInValue9.Text)
            Q2 = AreaToQ(DA)
            Sheets("Plot").Range("Discharge") = Q2: Sheets("Plot").Range("PipeSize") = TD2
            Call Plotlines(2, 4)
            

            D0 = Val(txtSediment) * TD / 100
            theta = Arccos((TD - 2 * D0) / TD)
            V = AreaToQ(DA) / PipeArea(TD, D0, theta)
        End If
         lblResult.Caption = "Velocity (f/s)"
        txtResult.Text = Format(V, "0.0")
    End Select
    Call GetChart
Exit Sub
ErrHandler:
    MsgBox "Please check your input data.", vbCritical, "Warning"
End Sub

Private Sub frmMain_close()
 Dim cht1 As Chart, ImageName As String, expt As Boolean
  Set cht1 = Sheets("Plot").ChartObjects("PicPlott").Chart
MsgBox ("lets's see")
   ImageName = ThisWorkbook.Path & "\temp1.jpg"
    If FileExists(ImageName) = False Then Kill ImageName
    End
End Sub

Private Sub cmdExit_Click()
 Dim cht1 As Chart, ImageName As String, expt As Boolean
  Set cht1 = Sheets("Plot").ChartObjects("PicPlott").Chart

   ImageName = ThisWorkbook.Path & "\temp1.jpg"
    If FileExists(ImageName) = False Then Kill ImageName
    End
End Sub

Private Sub cmdSaveGraph_Click()
frmMain.Height = 530
FramePlot.Width = 612: FramePlot.Height = 510
FramePlot.Visible = True

End Sub
Private Sub CommandButton1_Click()

Dim DownFile As String, ctitle As String
Savepath = GetFolder(ThisWorkbook.Path) + "\"

Dim cht1 As Chart, ImageName As String, expt As Boolean
  Set cht1 = Sheets("Plot").ChartObjects("PicPlott").Chart
  Sheets("Plot").ChartObjects("PicPlott").Chart.Refresh
   ImageName = ThisWorkbook.Path & "\temp1.jpg"
    expt = cht1.Export(ImageName, "jpg")


DownFile = Savepath & "DCoeff_" & Str(DC) & ".jpg"
FileCopy ImageName, DownFile
End Sub


Private Sub CommandButton2_Click()
FramePlot.Visible = False
FramePlot.Width = 342: FramePlot.Height = 390
frmMain.Height = 418
End Sub



Private Sub optClayConcrete_Click()
   txtOthersN.Visible = False
 '   Call DrawBasicLines
     frmMain.Caption = "Clay or Concrete Pipe"
      Sheets("Plot").Range("ptype") = 2
  Call SetChart: Call cmdCalculate_Click
     
End Sub

Private Sub optDC_1_Click()
    txtOthers.Visible = False
   lblDC.Caption = "Drainage Coefficient: 1 in/day"
  Sheets("Plot").Range("Dcap") = 1:
   Call SetChart: Call cmdCalculate_Click

End Sub

Private Sub optDC1_2_Click()
    txtOthers.Visible = False
   lblDC.Caption = "Drainage Coefficient: 1/2 in/day"
Sheets("Plot").Range("Dcap") = 0.5:
 Call SetChart: Call cmdCalculate_Click
 
End Sub


Private Sub optDC3_4_Click()
    txtOthers.Visible = False
   lblDC.Caption = "Drainage Coefficient: 3/4 in/day"
 Sheets("Plot").Range("Dcap") = 0.75:
  Call SetChart: Call cmdCalculate_Click

End Sub

Private Sub optDC3_8_Click()
   txtOthers.Visible = False
    lblDC.Caption = "Drainage Coefficient: 3/8 in/day"
   Sheets("Plot").Range("Dcap") = 0.375:
    Call SetChart: Call cmdCalculate_Click
End Sub


Private Sub optDInput0_Click()
        txtInValue0.Text = "4": txtInValue1.Text = "0.1": txtInValue1.Visible = True

        lblInputName0.Caption = "Tile Size (inch)"
        lblInputName1.Visible = True: lblInputName1.Caption = "Slope (%)"
End Sub

Private Sub optDInput1_Click()

 txtInValue0.Text = "0.5": txtInValue1.Text = "":: txtInValue1.Visible = False
 frmMain.lblInputName0.Caption = "Discharge (cfs)": frmMain.lblInputName1.Visible = False
End Sub

Private Sub optDInput2_Click()
        txtInValue0.Text = "4": txtInValue1.Text = "2": txtInValue1.Visible = True

        lblInputName0.Caption = "Tile Size (inch)"
        lblInputName1.Visible = True: lblInputName1.Caption = "Velocity (f/s)"
End Sub

Private Sub optDInput4_Click()
        txtInValue0.Text = "0.1": txtInValue1.Text = "2": txtInValue1.Visible = True

        lblInputName0.Caption = "Slope (%)"
        lblInputName1.Visible = True: lblInputName1.Caption = "Velocity (f/s)"
End Sub

Private Sub optDInput11_Click()
        txtInValue3.Text = "10": txtInValue2.Text = "0.1": txtInValue2.Visible = True

        lblInputName3.Caption = "Area (acre)"
        lblInputName2.Visible = True: lblInputName2.Caption = "Slope (%)"
End Sub
Private Sub optDInput9_Click()
        txtInValue3.Text = "0.5": txtInValue2.Text = "0.1": txtInValue2.Visible = True

        lblInputName3.Caption = "Discharge (cfs)"
        lblInputName2.Visible = True: lblInputName2.Caption = "Slope (%)"
End Sub
Private Sub optDInput7_Click()
        txtInValue3.Text = "0.1": txtInValue2.Text = "2": txtInValue2.Visible = True

        lblInputName3.Caption = "Slope (%)"
        lblInputName2.Visible = True: lblInputName2.Caption = "Velocity (f/s)"
End Sub
Private Sub optDInput17_Click()
    txtInValue5.Text = "10": txtInValue4.Text = "4": txtInValue4.Visible = True

    lblInputName5.Caption = "Area (acre)"
    lblInputName4.Visible = True: lblInputName4.Caption = "Tile Size (inch)"
End Sub

Private Sub optDInput13_Click()
        txtInValue5.Text = "4": txtInValue4.Text = "0.2": txtInValue4.Visible = True

        lblInputName5.Caption = "Tile Size (inch)"
        lblInputName4.Visible = True: lblInputName4.Caption = "Discharge (cfs)"
End Sub

Private Sub optDInput15_Click()
        txtInValue5.Text = "4": txtInValue4.Text = "2": txtInValue4.Visible = True

        lblInputName5.Caption = "Tile Size (inch)"
        lblInputName4.Visible = True: lblInputName4.Caption = "Velocity (f/s)"
End Sub

Private Sub optDInput23_Click()
        txtInValue7.Text = "4": txtInValue6.Text = "0.1": txtInValue6.Visible = True

        lblInputName70.Caption = "Tile Size (inch)"
        lblInputName60.Visible = True: lblInputName60.Caption = "Slope (%)"
End Sub
Private Sub optDInput22_Click()
        txtInValue7.Text = "10": txtInValue6.Text = "": txtInValue6.Visible = False

        lblInputName70.Caption = "Area (acre)"
        lblInputName60.Visible = False
End Sub

Private Sub optDInput21_Click()
        txtInValue7.Text = "4": txtInValue6.Text = "2": txtInValue6.Visible = True

        lblInputName70.Caption = "Tile Size (inch)"
        lblInputName60.Visible = True: lblInputName60.Caption = "Velocity (f/s)"
End Sub
Private Sub optDInput19_Click()
        txtInValue7.Text = "0.1": txtInValue6.Text = "2": txtInValue6.Visible = True

        lblInputName70.Caption = "Slope (%)"
        lblInputName60.Visible = True: lblInputName60.Caption = "Velocity (f/s)"
End Sub
Private Sub optDInput29_Click()
        txtInValue9.Text = "4": txtInValue8.Text = "0.1": txtInValue8.Visible = True

        lblInputName9.Caption = "Tile Size (inch)"
        lblInputName8.Visible = True: lblInputName8.Caption = "Slope (%)"
End Sub
Private Sub optDInput28_Click()
        txtInValue9.Text = "4": txtInValue8.Text = "0.2": txtInValue8.Visible = True

        lblInputName9.Caption = "Tile Size (inch)"
        lblInputName8.Visible = True: lblInputName8.Caption = "Discharge (cfs)"
End Sub
Private Sub optDInput27_Click()
        txtInValue9.Text = "4": txtInValue8.Text = "10": txtInValue8.Visible = True

        lblInputName9.Caption = "Tile Size (inch)"
        lblInputName8.Visible = True: lblInputName8.Caption = "Area (acre)"
End Sub


Private Sub optOtherM_Click()
    txtOthersN.Text = InputBox("Please Input Manning's Roughness of the Pipe.", "Manning's Roughness", "0.012")
    'If txtOthersN.Text = "" Then Exit Sub 'if Cancel button is pressed
    txtOthersN.Visible = True
    If txtOthersN.Text = "" Then txtOthersN.Text = "0.012"
 '   Call DrawBasicLines
     frmMain.Caption = "User Defined Tubing"
      Sheets("Plot").Range("ptype") = 4
  Call SetChart: Call cmdCalculate_Click
     
End Sub
Private Sub optOthers_Click()
    txtOthers.Text = InputBox("Please Input the Required Drainage Coefficient", "Drainage Coefficient", "0.125")
    'If txtOthers.Text = "" Then Exit Sub 'if Cancel button is pressed
    txtOthers.Visible = True
    If txtOthers.Text = "" Then txtOthers.Text = "0.125"
    lblDC.Caption = "Drainage Coefficient: " & txtOthers.Text & " in/day"
  Sheets("Plot").Range("Dcap") = Val(txtOthers.Text):
   Sheets("Plot").Range("ptype") = 1
 Call SetChart: Call cmdCalculate_Click
End Sub



Private Sub optPlastic_Click()
   txtOthersN.Visible = False
   ' Call DrawBasicLines
   ' picPlottingArea.Refresh

    frmMain.Caption = "Plastic Tubing"
 Sheets("Plot").Range("ptype") = 1

 Call SetChart: Call cmdCalculate_Click
End Sub

Private Sub optSmoothW_Click()
   txtOthersN.Visible = False
  '  Call DrawBasicLines
     frmMain.Caption = "Smooth Wall Pipe"
     
      Sheets("Plot").Range("ptype") = 3

 Call SetChart: Call cmdCalculate_Click
    
End Sub


Function Arccos(X)
    If X = 1 Then
        Arccos = 0
    Else
        Arccos = Atn(-X / Sqr(-X * X + 1)) + 2 * Atn(1)
    End If
End Function
Function Log10(X)
    Log10 = WorksheetFunction.Log(10) / Log(10)
End Function

Private Function DetDiaEq(ByVal x1 As Single, ByVal y1 As Single, ByVal x2 As Single, ByVal y2 As Single, ByVal ss As Single)
    'ss = slope in ft/ft
    
    Dim m As Single
    Dim b As Single
    
    ss = Log10(ss * 10000)
    
    m = (y2 - y1) / (x2 - x1)
    b = -m * x1 + y1
    DetDiaEq = m * (ss - x1) + y1
    'DetDiaEq = Log10(DetDiaEq * 100)
End Function
Private Function DetD(ByVal qq As Single)
    'qq=discharge in cfs
Dim DiaY1(1 To 14) As Single, DiaY2(1 To 14) As Single
    Dim I As Integer
    Dim DetY(1 To 14) As Single
    Dim x1 As Single, x2 As Single
    
    x1 = Log10(5): x2 = 3
    qq = Log10(qq * 100)
    
    For I = 1 To 14
        DetY(I) = DetDiaEq(x1, DiaY1(I), x2, DiaY2(I), S)
    Next I
    
    Select Case qq
        Case Is <= DetY(1): DetD = 3
        Case Is <= DetY(2): DetD = 4
        Case Is <= DetY(3): DetD = 5
        Case Is <= DetY(4): DetD = 6
        Case Is <= DetY(5): DetD = 8
        Case Is <= DetY(6): DetD = 10
        Case Is <= DetY(7): DetD = 12
        Case Is <= DetY(8): DetD = 15
        Case Is <= DetY(9): DetD = 18
        Case Is <= DetY(10): DetD = 21
        Case Is <= DetY(11): DetD = 24
        Case Is <= DetY(12): DetD = 30
        Case Is <= DetY(13): DetD = 36
        Case Is <= DetY(14): DetD = 42
        Case Else
            DetD = SecantMethod(3.5, 10) * 12 'Real tile dia in inch
    End Select
End Function
Function FindingDia(X As Single) As Single
    'X = dia. in ft
    Dim dd0 As Single
'    Dim pi As Single
    Dim theta1 As Single
    Dim ppArea As Single
    Dim wwp As Single
    Dim hhRadius As Single
    
    Pi = 4 * Atn(1)
    dd0 = Val(txtSediment) * X / 100
    theta1 = Arccos((X - 2 * dd0) / X)
    
    ppArea = (Pi - theta1) * X * X / 4 + (X - 2 * dd0) * X * Sin(theta1) / 4
    wwp = (Pi - theta1) * X + X * Sin(theta1)
    hhRadius = ppArea / wwp
    FindingDia = 1.486 / Roughness(X * 12) * ppArea * hhRadius ^ (2 / 3) * S ^ 0.5 - Q
End Function

Function SecantMethod(x0 As Single, x1 As Single) As Single
    'x = dia in ft
    Dim X As Single
    Dim Xold As Single
    Dim DeltaX As Single
    Dim Iter As Integer
    Const Tol = 0.0000001

    Xold = x0
    X = x1
    Iter = 0
    Do
        DeltaX = (X - Xold) / (1 - FindingDia(Xold) / FindingDia(X))
        Xold = X
        X = X - DeltaX
        Iter = Iter + 1
        If Iter > 5000 Then
            MsgBox "No Tile in range between 42 inch and 120 inch is found." & Chr(13) & Chr(13) & "Please check your input data.", vbExclamation, "Secant result"
            BDia = False
            Exit Function
        End If
    Loop Until Abs(DeltaX) < Tol
    SecantMethod = X 'tile dia. in ft
End Function





Private Sub picPlottingArea_Click()

End Sub

Private Sub SpinButton1_Change()
txtSediment.Text = SpinButton1.Value
End Sub



Private Sub txtOthers_Change()
Sheets("Plot").Range("Dcap") = Val(txtOthers.Text)
End Sub

Private Sub txtSediment_Change()
picPipe2.Height = Int((100 - Val(txtSediment.Text)) * 0.48)
Sheets("Plot").Range("Seddy") = Val(txtSediment.Text)
SpinButton1.Value = Val(txtSediment.Text)
End Sub

Private Sub SetChart()


Dim cht As Chart
Dim pt As Point
Dim p As Long
Dim dl As DataLabel
Dim srs As Series

Set cht = Sheets("Plot").ChartObjects("PicPlott").Chart
For ig = 1 To 20
p = 0
Set srs = cht.SeriesCollection(ig)
srs.HasDataLabels = False

  Set pt = srs.Points(2)
  pt.HasDataLabel = True
        Set dl = pt.DataLabel
        dl.Text = srs.Name


Next ig

For ig = 22 To 27
p = 0
Set srs = cht.SeriesCollection(ig)
srs.HasDataLabels = False

  Set pt = srs.Points(1)
  pt.HasDataLabel = True
        Set dl = pt.DataLabel
        dl.Text = srs.Name
        pt.DataLabel.Font.Name = "Arial"
        pt.DataLabel.Font.FontStyle = "Bold"
        pt.DataLabel.Font.Size = 11
        pt.DataLabel.Font.Color = RGB(0, 0, 255)

Next ig
   'lblDC.Caption = Sheets("Plot").Range("chtTitle")
cht.Refresh

End Sub




Public Sub GetChart()
'create .gif file of current  chart
Dim cht1 As Chart, ImageName As String, expt As Boolean
  Set cht1 = Sheets("Plot").ChartObjects("PicPlott").Chart

   ImageName = ThisWorkbook.Path & "\temp1.jpg"
    If FileExists(ImageName) = False Then Kill ImageName
    
  Sheets("Plot").ChartObjects("PicPlott").Visible = True
  Sheets("Plot").ChartObjects("PicPlott").Chart.Refresh
    expt = cht1.Export(ImageName, "jpg")
  Sheets("Plot").ChartObjects("PicPlott").Visible = False

    'set live data chart image to most recent image
frmMain.picPlottingArea.Picture = LoadPicture(ImageName)
FramePlot.Picture = LoadPicture(ImageName)


End Sub

Function FileExists(strfilename As String)
 
Dim strFileExists As String

    strFileExists = Dir(strfilename)
 
   If strFileExists = "" Then
        FileExists = True
    Else
        FileExists = False
    End If
 
End Function

Private Sub UserForm_Click()

End Sub
