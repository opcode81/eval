'''
Eval - the programmable calculator
(C) 2008-2010 by Dominik Jain (djain@gmx.net)
'''
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from __future__ import division # float division by default
from Tkinter import *
from ScrolledText import ScrolledText
import sys
import re
from math import *
import traceback

# --- functions ---

def avg(l):
    return float(sum(l))/len(l)

def itoa(n, base):
    chars = map(str, range(10)) + map(chr, range(ord('a'),ord('z')+1))
    digits = []
    while n > 0:
        digits.insert(0, chars[n % base])
        n /= base
    return "".join(digits)

# --- main class ---

class Eval:
    def __init__(self):
        self.vars = {}
        self.answers = []

    def calculate(self, command):
        cmd = command.strip()
        
        # replace answer variables and regular vars
        cmd = re.sub(r'a\[\s*(\d+)\s*\]', r'self.answers[int(\1)]', cmd) # replace "a[index]"
        cmd = re.sub(r'\ba\b', r'self.answers[int(-1)]', cmd) # replace "a"
        for var, value in self.vars.iteritems():
            cmd = re.sub(r'\b%s\b' % var, str(value), cmd)
        
        # check for output format modifier
        format = "normal"
        if cmd[-2:] == ",x":
            cmd = cmd[:-2]
            format = "hex"
        elif cmd[-2:] == ",b":
            cmd = cmd[:-2]
            format = "binary"
        
        # calculate and save result
        #print "Evaluating '%s'" % cmd
        try:
            result = eval(cmd)
        except:
            m = re.match(r'(\w+)\s*=(.*)', cmd)
            if m == None:                
                sys.stderr.write("Error evaluating '%s'\n" % cmd)
                return Eval.Result(sys.exc_info())
            else: # handle variable assignment
                try:
                    varname = m.group(1)
                    if varname in globals() or varname in dir(__builtins__):
                        raise Exception("'%s' is a reserved identifier" % varname)
                    result = eval(m.group(2))
                    self.vars[varname] = result                    
                except:
                    return Eval.Result(sys.exc_info())
        resultValue = result
        self.answers.append(resultValue)
        
        # format result
        if format == "normal":
            result = str(result)
        elif format == "hex":
            result = "0x%x %s" % (int(result), {True:"", False: "(rounded)"}[result==int(result)])
        elif format == "binary":
            result = "%sb %s" % (itoa(int(result), 2), {True:"", False: "(rounded)"}[result==int(result)])
        return Eval.Result(result, resultValue, len(self.answers)-1)
    
    class Result:
        def __init__(self, data, value = None, index = None):
            self.value = value
            self.data = data
            self.index = index
        
        def isError(self):
            return self.index is None
        
        def getErrorString(self):
            return str(self.data[1])
        
        def printError(self):
            traceback.print_exception(*self.data)

class EvalGUI:    
    def __init__(self, master):
        master.title("Eval")
      
        self.master = master
        self.frame = Frame(master)
        self.frame.pack(fill=BOTH, expand=1)

        self.fixed_width_font = ("Courier New", -12)
        self.frame.columnconfigure(0, weight=1)
        
        self.eval = Eval()

        # output control
        row = 0        
        self.out = ScrolledText(self.frame, wrap=NONE, bd=0, width=80, height=25, undo=1, maxundo=50, padx=5, pady=5, font=self.fixed_width_font)
        self.out.grid(row=row, column=0, sticky="NEWS")
        self.frame.rowconfigure(row, weight=1)

        # input control
        row += 1        
        self.commandEntry = EvalGUI.ExpressionEntry(self, master=self.frame, font=self.fixed_width_font)
        self.commandEntry.grid(row=row, column=0, sticky=EW)
        self.commandEntry.focus_set()
        
    def calculate(self, command):                
        result = self.eval.calculate(command)
        if result.isError(): return result
        self.out.insert(END, "a[%d] = %s = %s\n" % (result.index, command, result.data))
        self.out.yview_pickplace(END)        
        return result

    class ExpressionEntry(Entry):
        def __init__(self, eval, **args):
            self.evalInst = eval
            Entry.__init__(self, **args)
            self.history = []
            self.historyIdx = 1
            self.history0Text = ""
            self.bind('<Return>', self.onEnter)
            self.bind('<Up>', self.onUp)
            self.bind('<Down>', self.onDown)            
        
        def set(self, text):
            self.delete(0, len(self.get()))
            self.insert(0, text)
            self.select_range(0, len(text))
        
        def onEnter(self, event):
            command = self.get()
            self.history.append(command)
            result = self.evalInst.calculate(command)
            if not result.isError():
                self.select_range(0, len(command))
            else:
                result.printError()
                self.set(result.getErrorString())
            self.historyIdx = 1
        
        def onUp(self, event):
            self.setHistory(1)

        def onDown(self, event):
            self.setHistory(-1)

        def setHistory(self, change):
            if len(self.history) == 0: return
            # check if current content corresponds to history index, otherwise reset
            if self.get() != self.history[-self.historyIdx]:
                self.historyIdx = 0
            # remember user entry before using history
            if self.historyIdx == 0:
                self.history0Text = self.get()
            # set new history index
            self.historyIdx += change
            # check bounds
            if self.historyIdx < 0:
                self.historyIdx = 0
            elif self.historyIdx > len(self.history):
                self.historyIdx = len(self.history)
            # set new content
            if self.historyIdx == 0:
                self.set(self.history0Text)            
            else:
                self.set(self.history[-self.historyIdx])

class EvalShell:
    def __init__(self):
        self.eval = Eval()
        
    def run(self):
        while True:
            print "eval>> ",            
            command = sys.stdin.readline().strip()
            if command in ["", "exit", "quit"]: break
            result = self.eval.calculate(command)
            if result.isError():
                result.printError()
            else:
                print "a[%d] = %s = %s" % (result.index, command, result.data)

# -- main app --

if __name__ == '__main__':
    print "\nEval/Py (C) 2008-2012 by Dominik Jain <djain@gmx.net>\n"
    if "-s" in sys.argv: # shell mode
        EvalShell().run()
    else: # GUI mode
        print "option:  -s  shell/command line mode\n"
        try: 
            root = Tk()
        except:
            print "Warning: Tkinter not found or not usable, falling back to shell mode."
            EvalShell().run()
            sys.exit(0)
        gui = EvalGUI(root)
        root.mainloop()
        