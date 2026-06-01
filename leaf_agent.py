#!/usr/bin/env python#!/usr/bin/env python3
import os
import time
import requests
#!/usr/bin/env python3
import os
import time
import requests
from watchdog.observers import Observer
from watchdog.events#!/usr/bin/env python3
import os
import time
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
import json


class LabVaultLeafHandler(FileSystem#!/usr/bin/env python3
import os
import time
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
import json


class LabVaultLeafHandler(FileSystemEventHandler):
    def __init__(self,#!/usr/bin/env python3
import os
import time
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
import json


class LabVaultLeafHandler(FileSystemEventHandler):
    def __init__(self, api_url, device_code, operator_id=None):
        self.api_url = api_url
        self.device_code = device_code
        self#!/usr/bin/env python3
import os
import time
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
import json


class LabVaultLeafHandler(FileSystemEventHandler):
    def __init__(self, api_url, device_code, operator_id=None):
        self.api_url = api_url
        self.device_code = device_code
        self.operator_id = operator_id
        self.token =#!/usr/bin/env python3
import os
import time
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
import json


class LabVaultLeafHandler(FileSystemEventHandler):
    def __init__(self, api_url, device_code, operator_id=None):
        self.api_url = api_url
        self.device_code = device_code
        self.operator_id = operator_id
        self.token = None
        self.queue = []
        super().__init__()
    
    def login(self#!/usr/bin/env python3
import os
import time
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
import json


class LabVaultLeafHandler(FileSystemEventHandler):
    def __init__(self, api_url, device_code, operator_id=None):
        self.api_url = api_url
        self.device_code = device_code
        self.operator_id = operator_id
        self.token = None
        self.queue = []
        super().__init__()
    
    def login(self):
        # Leaf devices might need a different auth mechanism
        # For now, we'll#!/usr/bin/env python3
import os
import time
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
import json


class LabVaultLeafHandler(FileSystemEventHandler):
    def __init__(self, api_url, device_code, operator_id=None):
        self.api_url = api_url
        self.device_code = device_code
        self.operator_id = operator_id
        self.token = None
        self.queue = []
        super().__init__()
    
    def login(self):
        # Leaf devices might need a different auth mechanism
        # For now, we'll use a simple approach
        pass
    
    def on_created(self, event):
        if not#!/usr/bin/env python3
import os
import time
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
import json


class LabVaultLeafHandler(FileSystemEventHandler):
    def __init__(self, api_url, device_code, operator_id=None):
        self.api_url = api_url
        self.device_code = device_code
        self.operator_id = operator_id
        self.token = None
        self.queue = []
        super().__init__()
    
    def login(self):
        # Leaf devices might need a different auth mechanism
        # For now, we'll use a simple approach
        pass
    
    def on_created(self, event):
        if not event.is_directory:
            print(f"File created: {event.src_path}")
            self.process_file(event.src_path)
    
