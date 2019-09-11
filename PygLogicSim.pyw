import sys
sys.path.insert(0, "./PygGUI")
import PygCtl
from PygCtl import pygame, GREEN, BLACK, WHITE, RED
PygCtl.BKGR = (64,64,64)
GREY = (128, 128, 128)
BLUE = (0, 0, 255)


PortType = {"output": 1, "hybrid": 0, "input": -1}
LstPortType = ["input", "hybrid", "output"]
LstPortColors = [WHITE, GREY, BLACK]

LstExecNext = list()
LstAllExec = list()
NumTicks = 0
MAX_TPS = 500
CurTps = MAX_TPS
CurTpsMilli = 1000 / CurTps
MaxTpsMilli = 1000 / MAX_TPS
PrevSecTime = 0
def SimFunc(Evt):
    global LstExecNext
    global LstAllExec
    global TheTpsMon
    global NumTicks
    global CurTps
    global CurTpsMilli
    global PrevSecTime
    global MAX_TPS
    for Elem in LstAllExec:
        Elem.ExecOp()
    for Elem in LstExecNext:
        Elem.OnPortValChg()
    LstExecNext = list()
    CurTime = pygame.time.get_ticks()
    NumTicks += 1
    if CurTime - PrevSecTime >= 1000:
        if PygCtl.UsedTime == 0:
            if CurTps != MAX_TPS:
                CurTps = MAX_TPS
                CurTpsMilli = 1000 / CurTps
                pygame.time.set_timer(Evt.type, CurTpsMilli)
        elif 1000 / PygCtl.UsedTime != CurTps:
            CurTps = 1000 / PygCtl.UsedTime
            if CurTps > MAX_TPS: CurTps = MAX_TPS
            CurTpsMilli = 1000 / CurTps
            pygame.time.set_timer(Evt.type, CurTpsMilli)
        PrevSecTime = CurTime
        TheTpsMon.SetTps(NumTicks)
        NumTicks = 0
        PygCtl.UsedTime = 0
    return True
CurDragPort = None
def AddExecNext(Blk):
    global LstExecNext
    if not(Blk in LstExecNext): LstExecNext.append(Blk)
class Port(PygCtl.PygCtl):
    def __init__(self, Type, RelPos, Parent, Radius = 5):
        try:
            self.aType = PortType[Type]
        except: self.aType = Type
        self.Val = 0
        self.Radius = Radius
        self.Width = 0
        self.RelPos = RelPos
        self.Parent = Parent
        self.CalcAbsPos()
        self.Color = LstPortColors[self.aType + 1]
        self.PrevPos = None
        self.bType = self.aType
        self.OpTypePorts = list()
        self.LstConn = list()
        self.Dir = 0
        self.MaxFanOut = -1
        self.PrevRad = self.Radius + self.Width
        self.PrevRect = None#for proper dirty redraw that the base class provides
    def __repr__(self):
        return "Port(" + repr(LstPortType[self.aType + 1]) + ", " + repr(self.Pos) + ", " + repr(self.Parent) + ", " + repr(self.Radius) + ")"
    def __str__(self):
        return "Port of type: " + LstPortType[self.aType + 1] + "\n  and radius: " + str(self.Radius) + "\n  at position: " + str(self.Pos)
    def PreDraw(self, Surf):
        #print "predraw: " + str(self.Parent.LstPorts.index(self))
        if self.PrevPos != None: return [pygame.draw.circle(Surf, PygCtl.BKGR, self.PrevPos, self.PrevRad)]
        return []
    def Draw(self, Surf):
        #print "draw: " + str(self.Parent.LstPorts.index(self))
        self.PrevPos = self.Pos
        self.PrevRad = self.Radius + self.Width
        self.PrevRect = pygame.draw.circle(Surf, self.Color, self.Pos, self.Radius + self.Width)
        return [self.PrevRect]
    def DirtyRedraw(self, Surf, LstRects):
        if self.PrevRect == None: return []
        Rtn = []
        if self.PrevRect.collidelistall(LstRects) != -1:
            Rtn = self.PreDraw(Surf)
            Rtn.extend(self.Draw(Surf))
        return Rtn
    def CollidePt(self, Pt):
        return PygCtl.CollidePtCircle(Pt, self.Pos, self.Radius + 3)
    def OnMouseEnter(self):
        self.Width = 1
        #PygCtl.SetRedraw(self.Parent)
        return True
    def OnMouseExit(self):
        self.Width = 0
        #PygCtl.SetRedraw(self.Parent)
        return True
    def ChgPortType(self, Type, FromLst):
        if self.bType == Type: return None
        if self.aType != 0: return None
        self.bType = Type
        if FromLst:
            for Conn in self.LstConn:
                Conn.GetOtherPort(self).ChgPortType(-Type, False)
        else:
            for ThePort in self.OpTypePorts:
                ThePort.ChgPortType(-Type, True)
    def CanAcceptConn(self):
        return self.MaxFanOut < 0 or len(self.LstConn) < self.MaxFanOut
    def Rotate(self, ClkWise = True):
        if ClkWise: self.RelPos = 1.0 - self.RelPos[1], self.RelPos[0]
        else: self.RelPos = self.RelPos[1], 1.0 - self.RelPos[0]
        self.CalcAbsPos()
        for Conn in self.LstConn: Conn.RouteConn()
        PygCtl.SetRedraw(self)
    def OnEvt(self, Evt, Pos):
        global CurDragPort
        if Evt.type == pygame.MOUSEBUTTONDOWN and Evt.button == 1:
            CurDragPort = self
        elif Evt.type == pygame.MOUSEBUTTONUP and Evt.button == 1:
            if CurDragPort != None and CurDragPort != self:
                Src = CurDragPort
                CurDragPort = None
                if Src.CanAcceptConn() and self.CanAcceptConn() and (Src.aType == -self.aType or Src.aType == 0 or self.aType == 0):
                    Connection(self, Src)
            else: CurDragPort = None
        return False
    def SetVal(self, Val, FromParen = True):
        if FromParen:
            if self.Val != Val and self.bType != 1: AddExecNext(self.Parent)
            self.Val = Val
            if self.bType == 1:
                for Conn in self.LstConn:
                    Conn.SetConnVal(Val, self)
        elif self.Val != Val and self.bType != 1:
            self.Val = Val
            AddExecNext(self.Parent)
    def CalcAbsPos(self):
        self.Pos = (
            int(self.RelPos[0] * self.Parent.DrawObj.GetSize()[0] + self.Parent.Pos[0]),
            int(self.RelPos[1] * self.Parent.DrawObj.GetSize()[1] + self.Parent.Pos[1]))
    def ChgParenPos(self):
        self.CalcAbsPos()
        for Conn in self.LstConn: Conn.RouteConn()
        PygCtl.SetRedraw(self)
    def Remove(self):
        self.Color = PygCtl.BKGR
        for Conn in self.LstConn: Conn.Remove()
        try:
            PygCtl.LstCtl.remove(self)
        except:
            pass
        PygCtl.SetRedraw(self)
"""def ManhattanRouter(Src, Tgt):
    Rtn = [Tgt.Pos, Src.Pos]
    if (Tgt.Dir - Src.Dir) % 4 != 2:
        Pos = None
        if ((Tgt.Dir == 3 and Tgt.Pos[1] > Src.Pos[1]) or (Tgt.Dir == 1 and Tgt.Pos[1] <= Src.Pos[1])) and ((Src.Dir == 0 and Tgt.Pos[0] > Src.Pos[0]) or (Src.Dir == 2 and Tgt.Pos[0] <= Src.Pos[0])):
            Pos = [(Tgt.Pos[0], Src.Pos[1])]
        elif ((Src.Dir == 3 and Src.Pos[1] > Tgt.Pos[1]) or (Src.Dir == 1 and Src.Pos[1] <= Tgt.Pos[1])) and ((Tgt.Dir == 0 and Src.Pos[0] > Tgt.Pos[0]) or (Tgt.Dir == 2 and Src.Pos[0] <= Tgt.Pos[0])):
            Pos = [(Src.Pos[0], Tgt.Pos[1])]
        elif Src.Dir == Tgt.Dir and Src.Dir % 2 == 0:#x axis
            if Src.Dir == 0 and Src.Pos[0] < Tgt.Pos[0]
        elif Src.Dir == Tgt.Dir and Src.Dir % 2 == 1:#y axis
    if Tgt.Pos[0] == Src.Pos[0]: return Rtn
    elif Tgt.Pos[1] == Src.Pos[1]: return Rtn
    else:
        
        Rtn.insert("""
def DirectRouter(Src, Tgt):
    return [Tgt.Pos, Src.Pos]
class LogicWire(PygCtl.Wire):
    def __init__(self, LstPts, Color, Conn):
        super(LogicWire, self).__init__(LstPts, Color)
        self.Conn = Conn
    def OnEvt(self, Evt, Pos):
        if Evt.type == pygame.KEYDOWN:
            if Evt.key == pygame.K_DELETE:
                try:
                    PygCtl.LstCtl.remove(self)
                    self.Conn.Remove()
                    self.Color = PygCtl.BKGR
                except: return False
                return True
        return False
    def SetColor(self, Color):
        if self.Color == Color: return None
        self.Color = Color
        PygCtl.SetRedraw(self)
AfterZIndex = 0
class Connection:
    def __init__(self, Tgt, Src, Router = DirectRouter):
        self.Tgt = Tgt
        self.Src = Src
        self.Tgt.OpTypePorts.append(Src)
        self.Src.OpTypePorts.append(Tgt)
        Src.LstConn.append(self)
        Tgt.LstConn.append(self)
        self.Router = Router
        self.TheWire = LogicWire(self.Router(Src, Tgt), RED, self)
        PygCtl.LstCtl.insert(AfterZIndex, self.TheWire)
        if Tgt.bType > 0:
            Src.ChgPortType(-Tgt.bType, False)
            self.SetConnVal(Tgt.Val, Tgt)
        elif Src.bType > 0:
            Tgt.ChgPortType(-Src.bType, False)
            self.SetConnVal(Src.Val, Src)
    def GetOtherPort(self, Cur):
        if self.Tgt == Cur: return self.Src
        return self.Tgt
    def Remove(self):
        try: self.Tgt.OpTypePorts.remove(self.Src)
        except: pass
        try: self.Src.OpTypePorts.remove(self.Tgt)
        except: pass
        try: self.Tgt.LstConn.remove(self)
        except: pass
        try: self.Src.LstConn.remove(self)
        except: pass
        if self.Tgt.bType < 0:
            self.Tgt.ChgPortType(0, False)
            self.Tgt.SetVal(0, False)
        elif self.Src.bType < 0:
            self.Src.ChgPortType(0, False)
            self.Src.SetVal(0, False)
        try:
            PygCtl.LstCtl.remove(self.TheWire)
        except:
            pass
    def SetConnVal(self, Val, Ignore = None):
        if Val == 1: self.TheWire.SetColor(GREEN)
        else: self.TheWire.SetColor(RED)
        if Ignore != None:
            if self.Src == Ignore: return self.Tgt.SetVal(Val, False)#returning None to shorten code
            elif self.Tgt == Ignore: return self.Src.SetVal(Val, False)
        self.Src.SetVal(Val, False)
        self.Tgt.SetVal(Val, False)
    def RouteConn(self):
        self.TheWire.LstPts = self.Router(self.Src, self.Tgt)
        PygCtl.SetRedraw(self.TheWire)
class Drawable(object):
    def Draw(self, Surf, Pos):
        return []
    def GetSize(self):
        return (0,0)
    def Rotate(self, IsClkWise):
        pass
class Image(Drawable):
    def __init__(self, Img):
        self.Img = Img
    def Draw(self, Surf, Pos):
        return Surf.blit(self.Img, Pos)
    def GetSize(self):
        return self.Img.get_size()
    def Rotate(self, IsClkWise):
        Angle = 90
        if IsClkWise: Angle = -Angle
        self.Img = pygame.transform.rotate(self.Img, Angle)
class DrawRect(Drawable):
    def __init__(self, Color, Width, Height):
        self.Size = (Width, Height)
        self.Color = Color
    def Draw(self, Surf, Pos):
        return Surf.fill(self.Color, pygame.rect.Rect(Pos, self.Size))
    def GetSize(self):
        return self.Size
    def Rotate(self, IsClkWise):
        self.Size = self.Size[1], self.Size[0]
class Draw2Rect(Drawable):
    def __init__(self, Color, iColor, Width, Height, iWidth, iHeight):
        self.Size = (Width, Height)
        self.Color = Color
        self.iColor = iColor
        self.iSize = (iWidth, iHeight)
        self.iOff = (Width - iWidth) / 2, (Height - iHeight) / 2
    def Draw(self, Surf, Pos):
        Rtn = Surf.fill(self.Color, pygame.rect.Rect(Pos, self.Size))
        iRect = pygame.rect.Rect((Pos[0] + self.iOff[0], Pos[1] + self.iOff[1]), self.iSize)
        Surf.fill(self.iColor, iRect)
        return Rtn
    def GetSize(self):
        return self.Size
    def Rotate(self, IsClkWise):
        self.Size = self.Size[1], self.Size[0]
        self.iSize = self.iSize[1], self.iSize[0]
        self.iOff = (self.Size[0] - self.iSize[0]) / 2, (self.Size[1] - self.iSize[1]) / 2
class PortData:
    def __init__(self, Type, RelPos):
        self.Type = Type
        self.Pos = RelPos
class Block(PygCtl.PygCtl):
    def __init__(self, LstPorts, OpFunc, DrawObj, Pos):
        global LstAllExec
        self.LstPorts = [None] * len(LstPorts)
        self.Pos = Pos
        self.DrawObj = DrawObj
        for c in xrange(len(LstPorts)):
            self.LstPorts[c] = Port(LstPorts[c].Type, LstPorts[c].Pos, self)
        self.TotRect = pygame.rect.Rect(self.Pos, self.DrawObj.GetSize())
        self.PrevRect = None
        self.Time = 1
        self.Delay = 1
        self.CurOff = None
        self.OpFunc = OpFunc
        self.ExecOp()
        self.Time = 0
        self.LstPrevRects = list()
        LstAllExec.append(self)
    def CollidePt(self, Pt):
        Rtn = self.TotRect.collidepoint(Pt)
        if not Rtn: return Rtn
        for ThePort in self.LstPorts:
            if ThePort.CollidePt(Pt): return False
        return Rtn
    #called on mouse down to determine whether or not to start drag
    def CollidePtDrag(self, xOff, yOff):#Default is always drag
        return True
    def PreDraw(self, Surf):
        if self.PrevRect != None: return [Surf.fill(PygCtl.BKGR, self.PrevRect)]
        return []
    def Draw(self, Surf):
        self.PrevRect = self.DrawObj.Draw(Surf, self.Pos)
        return [self.PrevRect]
    def OnDrag(self):
        pass
    def OnDragEnd(self):
        pass
    def Remove(self):
        for ThePort in self.LstPorts: ThePort.Remove()
        try:
            PygCtl.LstCtl.remove(self)
        except:
            pass
        try:
            LstAllExec.remove(self)
        except:
            pass
    def OnEvt(self, Evt, Pos):
        if Evt.type == pygame.MOUSEBUTTONDOWN and Evt.button == 1:
            xOff = Pos[0] - self.Pos[0]
            yOff = Pos[1] - self.Pos[1]
            if self.CollidePtDrag(xOff, yOff):
                self.CurOff = (-xOff, -yOff)
                self.OnDrag()
                return True
            else: return False
        elif self.CurOff != None and Evt.type == pygame.MOUSEBUTTONUP and Evt.button == 1:
            self.CurOff = None
            self.OnDragEnd()
            return True
        elif Evt.type == pygame.KEYDOWN:
            if Evt.key == pygame.K_r:
                self.Rotate(Evt.mod & pygame.KMOD_SHIFT == 0)
                return True
            elif Evt.key == pygame.K_DELETE:
                self.Remove()
                Size = self.DrawObj.GetSize()
                self.DrawObj = DrawRect(PygCtl.BKGR, Size[0], Size[1])
                return True
            return False
        else: return False
    def OnEvtGlobal(self, Evt):
        if self.CurOff != None and Evt.type == pygame.MOUSEMOTION:
            return self.ChgPos((Evt.pos[0] + self.CurOff[0], Evt.pos[1] + self.CurOff[1]))
        else: return False
    def Rotate(self, IsClkWise = True):
        Width, Height = self.DrawObj.GetSize()
        Center = self.Pos[0] + Width / 2.0, self.Pos[1] - Height / 2.0
        self.Pos = Width / 2.0, Height / 2.0
        if IsClkWise: self.Pos = Center[0] - self.Pos[1], Center[1] + self.Pos[0]
        else: self.Pos = -self.Pos[1] + Center[0], self.Pos[0] + Center[1]
        self.DrawObj.Rotate(IsClkWise)
        self.TotRect = pygame.rect.Rect(self.Pos, self.DrawObj.GetSize())
        for ThePort in self.LstPorts: ThePort.Rotate(IsClkWise)
    def ExecOp(self):
        if self.OpFunc == None: return None
        if self.Time > 0:
            self.Time -= 1
            if self.Time <= 0: self.OpFunc(self.LstPorts)
    def ChgPos(self, Pos):
        self.Pos = Pos
        self.TotRect = pygame.rect.Rect(self.Pos, self.DrawObj.GetSize())
        c = 0
        for ThePort in self.LstPorts:
            #print "ChgParenPos " + str(c) + " " + str(ThePort in PygCtl.LstCtl)
            ThePort.ChgParenPos()
            c += 1
        return True
    def OnPortValChg(self):
        self.Time = self.Delay
def Blend(Src, AlphaColor, AlphaVal):
    AlphaVal = float(AlphaVal) / 255
    return int((1 - AlphaVal) * Src + AlphaColor * AlphaVal)
def BlendColor(Src, AlphaColor, AlphaVal):
    AlphaVal = float(AlphaVal) / 255
    Rtn = [0] * len(Src)
    for c in xrange(len(Src)):
        Rtn[c] = int((1 - AlphaVal) * Src[c] + AlphaColor[c] * AlphaVal)
    return tuple(Rtn)
LstStateColor = [RED, GREEN]
class InputBlock(Block):
    def __init__(self, Pos, Width, Height):
        self.State = 0
        self.iWidth = Width / 2
        self.iHeight = Height / 2
        self.cWidth = self.iWidth / 2
        self.cHeight = self.iHeight / 2
        self.Width = Width
        self.Height = Height
        DrawObj = Draw2Rect(RED, BLACK, Width, Height, self.iWidth, self.iHeight)
        super(InputBlock, self).__init__([PortData("output", (1, .5))], None, DrawObj, Pos)
    def OnDrag(self):
        self.DrawObj.Color = BlendColor(self.DrawObj.Color, WHITE, 64)
    def OnDragEnd(self):
        self.DrawObj.Color = LstStateColor[self.State]
    def CollidePtDrag(self, xOff, yOff):
        if xOff < self.cWidth: return True
        elif self.Width - xOff < self.cWidth: return True
        elif yOff < self.cHeight: return True
        elif self.Height - yOff < self.cHeight: return True
        else: return False
    def OnEvt(self, Evt, Pos):
        if Evt.type == pygame.MOUSEBUTTONDOWN and Evt.button == 1:
            if self.CollidePtDrag(Pos[0] - self.Pos[0], Pos[1] - self.Pos[1]):
                return super(InputBlock, self).OnEvt(Evt, Pos)
            self.State += 1
            self.State %= 2
            self.DrawObj.Color = LstStateColor[self.State]
            for ThePort in self.LstPorts: ThePort.SetVal(self.State)
            return True
        elif self.CurOff != None: return super(InputBlock, self).OnEvt(Evt, Pos)
        else: return super(InputBlock, self).OnEvt(Evt, Pos)
    def ExecOp(self):
        pass
    def OnPortValChg(self):
        pass
class OutputBlock(Block):
    def __init__(self, Pos, Width, Height):
        self.Width = Width
        self.Height = Height
        self.CurOff = None
        self.State = 0
        DrawObj = DrawRect(RED, Width, Height)
        super(OutputBlock, self).__init__([PortData("input", (0, .5))], None, DrawObj, Pos)
    def OnDrag(self):
        self.DrawObj.Color = BlendColor(self.DrawObj.Color, WHITE, 64)
    def OnDragEnd(self):
        self.DrawObj.Color = LstStateColor[self.State]
    def ExecOp(self):
        if self.Time > 0:
            self.Time -= 1
            if self.Time <= 0:
                self.State = 0
                for ThePort in self.LstPorts:
                    if ThePort.aType == -1 and ThePort.Val == 1:
                        self.State = 1
                        break
                self.DrawObj.Color = LstStateColor[self.State]
                PygCtl.SetRedraw(self)
def AddBlock(Blk):
    PygCtl.LstCtl.insert(AfterZIndex, Blk)
    PygCtl.SetRedraw(Blk)
    for ThePort in Blk.LstPorts:
        PygCtl.LstCtl.insert(AfterZIndex, ThePort)
        PygCtl.SetRedraw(ThePort)
class GateMaker(PygCtl.PygCtl):
    def __init__(self, Img, Pos, FuncMkGate):
        self.ImgBtn = Img
        self.ImgDrag = Img.copy()
        self.ImgDrag.set_alpha(127)
        self.DragChg = False
        self.DragPos = None
        self.Pos = Pos
        self.PrevRect = [None, None]
        self.TotRect = pygame.rect.Rect(Pos, Img.get_size())
        self.ActFunc = FuncMkGate
        self.PrevSurf = None
    def PreDraw(self, Surf):
        Rtn = []
        if self.PrevRect[0] != None:
            Rtn.append(Surf.fill(PygCtl.BKGR, self.PrevRect[0]))
        if self.PrevRect[1] != None:
            Rtn.append(Surf.fill(PygCtl.BKGR, self.PrevRect[1]))
        return Rtn
    def Draw(self, Surf):
        Rtn = []
        if self.DragPos != None:
            self.PrevRect[0] = Surf.blit(self.ImgDrag, self.DragPos)
            Rtn.append(self.PrevRect[0])
        else: self.PrevRect[0] = None
        self.PrevRect[1] = Surf.blit(self.ImgBtn, self.Pos)
        Rtn.append(self.PrevRect[1])
        return Rtn
    def OnEvt(self, Evt, Pos):
        if Evt.type == pygame.MOUSEBUTTONDOWN and Evt.button == 1:
            self.DragChg = True
            self.DragPos = Pos
            return True
        return False
    def OnEvtGlobal(self, Evt):
        if self.DragPos != None and Evt.type == pygame.MOUSEMOTION:
            self.DragPos = Evt.pos
            self.DragChg = True
            return True
        elif self.DragPos != None and Evt.type == pygame.MOUSEBUTTONUP and Evt.button == 1:
            self.DragPos = None
            self.DragChg = False
            if not self.CollidePt(Evt.pos): AddBlock(self.ActFunc(Evt.pos))
            return True
        return False
    def CollidePt(self, Pt):
        return self.TotRect.collidepoint(Pt)
def NPortAnd(LstPorts):
    Rtn = True
    OutPort = None
    for ThePort in LstPorts:
        if ThePort.aType == -1:
            Rtn = Rtn and bool(ThePort.Val)
        elif ThePort.aType == 1:
            OutPort = ThePort
        if not Rtn and OutPort != None:
            break
    OutPort.SetVal(int(Rtn))
def NPortNand(LstPorts):
    Rtn = True
    OutPort = None
    for ThePort in LstPorts:
        if ThePort.aType == -1:
            Rtn = Rtn and bool(ThePort.Val)
        elif ThePort.aType == 1:
            OutPort = ThePort
        if not Rtn and OutPort != None:
            break
    OutPort.SetVal(int(not Rtn))
def NPortXor(LstPorts):
    Rtn = 0
    OutPort = None
    for ThePort in LstPorts:
        if ThePort.aType == -1:
            Rtn += ThePort.Val
            Rtn %= 2
        elif ThePort.aType == 1:
            OutPort = ThePort
    OutPort.SetVal(Rtn)
def NPortXnor(LstPorts):
    Rtn = 0
    OutPort = None
    for ThePort in LstPorts:
        if ThePort.aType == -1:
            Rtn += ThePort.Val
            Rtn %= 2
        elif ThePort.aType == 1:
            OutPort = ThePort
    Rtn = int(not bool(Rtn))
    OutPort.SetVal(Rtn)
def NPortOr(LstPorts):
    Rtn = False
    OutPort = None
    for ThePort in LstPorts:
        if ThePort.aType == -1:
            Rtn = Rtn or bool(ThePort.Val)
        elif ThePort.aType == 1:
            OutPort = ThePort
        if Rtn and OutPort != None:
            break
    OutPort.SetVal(int(Rtn))
def NPortNor(LstPorts):
    Rtn = False
    OutPort = None
    for ThePort in LstPorts:
        if ThePort.aType == -1:
            Rtn = Rtn or bool(ThePort.Val)
        elif ThePort.aType == 1:
            OutPort = ThePort
        if Rtn and OutPort != None:
            break
    OutPort.SetVal(int(not Rtn))
TwoPortData = [
    PortData("input", (0, .25)),
    PortData("input", (0, .75)),
    PortData("output", (1, .5))]
def MkAnd2(Pos):
    global TwoPortData
    global AndImg
    return Block(TwoPortData, NPortAnd, Image(AndImg), Pos)
def MkNand2(Pos):
    global TwoPortData
    global NandImg
    return Block(TwoPortData, NPortNand, Image(NandImg), Pos)
def MkXor2(Pos):
    global TwoPortData
    global XorImg
    return Block(TwoPortData, NPortXor, Image(XorImg), Pos)
def MkXnor2(Pos):
    global TwoPortData
    global XnorImg
    return Block(TwoPortData, NPortXnor, Image(XnorImg), Pos)
def MkOr2(Pos):
    global TwoPortData
    global OrImg
    return Block(TwoPortData, NPortOr, Image(OrImg), Pos)
def MkNor2(Pos):
    global TwoPortData
    global NorImg
    return Block(TwoPortData, NPortNor, Image(NorImg), Pos)
def Mk32Src(Pos):
    return InputBlock(Pos, 32, 32)
def Mk64Src(Pos):
    return InputBlock(Pos, 64, 64)
def Mk32Tgt(Pos):
    return OutputBlock(Pos, 32, 32)
def Mk64Tgt(Pos):
    return OutputBlock(Pos, 64, 64)
if __name__ == "__main__":
    PygCtl.Init(pygame.RESIZABLE)
    TxtFnt = pygame.font.SysFont("Courier New", 40)
    AndImg = TxtFnt.render("AND", 0, GREEN, BLUE)
    NandImg = TxtFnt.render("NAND", 0, GREEN, BLUE)
    XorImg = TxtFnt.render("XOR", 0, GREEN, BLUE)
    XnorImg = TxtFnt.render("XNOR", 0, GREEN, BLUE)
    OrImg = TxtFnt.render("OR", 0, GREEN, BLUE)
    NorImg = TxtFnt.render("NOR", 0, GREEN, BLUE)
    Src32Img = pygame.Surface((32, 32))
    Src32Img.fill(RED)
    Tgt32Img = Src32Img.copy()
    Src32Img.fill(BLACK, pygame.rect.Rect(8, 8, 16, 16))
    Src64Img = pygame.Surface((64, 64))
    Src64Img.fill(RED)
    Tgt64Img = Src64Img.copy()
    Src64Img.fill(BLACK, pygame.rect.Rect(16, 16, 32, 32))
    #AddBlock(InputBlock((100, 100), 64, 64))
    #AddBlock(InputBlock((100, 200), 64, 64))
    #AddBlock(OutputBlock((200, 100), 64, 64))
    #AddBlock(OutputBlock((200, 200), 64, 64))
    #AddBlock(MkNor2((300, 100)))
    #AddBlock(MkNor2((300, 200)))
    LstGateFuncs = [
        (Src32Img, Mk32Src),
        (Tgt32Img, Mk32Tgt),
        (Src64Img, Mk64Src),
        (Tgt64Img, Mk64Tgt),
        (AndImg, MkAnd2),
        (NandImg, MkNand2),
        (XorImg, MkXor2),
        (XnorImg, MkXnor2),
        (OrImg, MkOr2),
        (NorImg, MkNor2)]
    CurPos = [0, 20]
    TpsClk = pygame.time.Clock()
    for Gate in LstGateFuncs:
        PygCtl.LstCtl.append(GateMaker(Gate[0], tuple(CurPos), Gate[1]))
        CurPos[1] += Gate[0].get_height() + 2
    TheTpsMon = PygCtl.TpsMon(TxtFnt, (255, 255, 0), (CurPos[0] + 120, CurPos[1]))
    PygCtl.LstCtl.append(TheTpsMon)
    AfterZIndex = len(PygCtl.LstCtl)
    PygCtl.DctEvtFunc[pygame.USEREVENT] = SimFunc
    pygame.time.set_timer(pygame.USEREVENT, 1000 / CurTps)
    PygCtl.RunCtls()
    pygame.time.set_timer(pygame.USEREVENT, 0)
    pygame.quit()
