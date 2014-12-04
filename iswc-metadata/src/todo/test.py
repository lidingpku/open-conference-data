import os
import mu.mutil

print os.path.dirname(__file__)

config = mu.mutil.config_load(file_home=__file__)
print config
