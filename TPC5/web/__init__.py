import os, sys; 
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
# sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))

##### ============== UNCOMMENT BELOW TO TRACE PRINTS ==============
# import sys
# import traceback

# class TracePrints(object):
#   def __init__(self):    
#     self.stdout = sys.stdout
#   def write(self, s):
#     self.stdout.write("Writing %r\n" % s)
#     traceback.print_stack(file=self.stdout)
#   def flush(self):
#     self.stdout.flush()

# sys.stdout = TracePrints()
