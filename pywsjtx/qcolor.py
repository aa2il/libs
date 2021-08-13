#
# Utility class to help out with Qt Color Values.
#
#
# Here is a nice color picker:
#    https://www.rapidtables.com/web/color/RGB_Color.html
# 

class QCOLOR:
    SPEC_RGB = 1
    SPEC_INVALID = 0

    def __init__(self, spec, alpha, red, green, blue):
        self.spec = spec
        self.red = red
        self.green = green
        self.blue = blue
        self.alpha = alpha

    @classmethod
    def Black(cls):
        return QCOLOR(QCOLOR.SPEC_RGB, 255, 0, 0, 0)

    @classmethod
    def Red(cls):
        return QCOLOR(QCOLOR.SPEC_RGB, 255, 255, 0, 0)

    @classmethod
    def Pink(cls):
        return QCOLOR(QCOLOR.SPEC_RGB, 255, 255, 204, 204)

    @classmethod
    def Green(cls):
        return QCOLOR(QCOLOR.SPEC_RGB, 255, 0, 255, 0)

    @classmethod
    def LightGreen(cls):
        return QCOLOR(QCOLOR.SPEC_RGB, 255, 153, 255, 153)

    @classmethod
    def Blue(cls):
        return QCOLOR(QCOLOR.SPEC_RGB, 255, 0, 0, 255)

    @classmethod
    def LightBlue(cls):
        return QCOLOR(QCOLOR.SPEC_RGB, 255, 204, 204, 255)

    @classmethod
    def Cyan(cls):
        return QCOLOR(QCOLOR.SPEC_RGB, 255, 0, 255, 255)

    @classmethod
    def LightCyan(cls):
        return QCOLOR(QCOLOR.SPEC_RGB, 255, 204, 255, 255)

    @classmethod
    def Magenta(cls):
        return QCOLOR(QCOLOR.SPEC_RGB, 255, 255, 0, 255)

    @classmethod
    def LightMagenta(cls):
        return QCOLOR(QCOLOR.SPEC_RGB, 255, 255, 204, 255)

    @classmethod
    def Purple(cls):
        return QCOLOR(QCOLOR.SPEC_RGB, 255, 127, 0, 255)

    @classmethod
    def LightPurple(cls):
        return QCOLOR(QCOLOR.SPEC_RGB, 255, 229, 204, 255)

    @classmethod
    def Gray(cls):
        return QCOLOR(QCOLOR.SPEC_RGB, 255, 127, 127, 127)

    @classmethod
    def LightGray(cls):
        return QCOLOR(QCOLOR.SPEC_RGB, 255, 224, 224, 224)

    @classmethod
    def Yellow(cls):
        return QCOLOR(QCOLOR.SPEC_RGB, 255, 255, 255, 0)

    @classmethod
    def LightYellow(cls):
        return QCOLOR(QCOLOR.SPEC_RGB, 255, 255, 255, 204)

    @classmethod
    def RGBA(cls, alpha, red, green, blue):
        return QCOLOR(QCOLOR.SPEC_RGB, alpha, red, green, blue)

    @classmethod
    def White(cls):
        return QCOLOR(QCOLOR.SPEC_RGB, 255,255,255,255)

    @classmethod
    def Uncolor(cls):
        return QCOLOR(QCOLOR.SPEC_INVALID, 0,0,0,0)

    @classmethod
    def COLORS(cls,idx):
        
        if idx==0:
            return cls.Uncolor()
        elif idx==1:
            return cls.Red()
        elif idx==2:
            return cls.Green()
        elif idx==3:
            return cls.Blue()
        elif idx==4:
            return cls.Cyan()
        elif idx==5:
            return cls.Magenta()
        elif idx==6:
            return cls.Yellow()
        elif idx==7:
            return cls.Black()
        elif idx==8:
            return cls.White()
        elif idx==9:
            return cls.Pink()
        elif idx==10:
            return cls.LightGreen()
        elif idx==11:
            return cls.LightBlue()
        elif idx==12:
            return cls.LightCyan()
        elif idx==13:
            return cls.LightMagenta()
        elif idx==14:
            return cls.LightYellow()
        elif idx==15:
            return cls.Gray()
        elif idx==16:
            return cls.LightGray()
        elif idx==17:
            return cls.Purple()
        elif idx==18:
            return cls.LightPurple()
        else:
            print('PYWSJTX QCOLOR - Unknown color index')
            return cls.Uncolor()

    
        
            

