import os
import shutil

banner = """
______       __  __ _       _____       _         _   _           _       _            
| ___ \     / _|/ _(_)     /  __ \     (_)       | | | |         | |     | |           
| |_/ /   _| |_| |_ _ _ __ | /  \/ ___  _ _ __   | | | |_ __   __| | __ _| |_ ___ _ __ 
|  __/ | | |  _|  _| | '_ \| |    / _ \| | '_ \  | | | | '_ \ / _` |/ _` | __/ _ \ '__|
| |  | |_| | | | | | | | | | \__/\ (_) | | | | | | |_| | |_) | (_| | (_| | ||  __/ |   
\_|   \__,_|_| |_| |_|_| |_|\____/\___/|_|_| |_|  \___/| .__/ \__,_|\__,_|\__\___|_|   
                                                       | |                             
                                                       |_|                             
"""

print(banner)


cwd = os.getcwd() #Get working directory

os.system("git clone https://github.com/PuffinDev/PuffinCoin temp") #Clone repo into temp

try:
    shutil.rmtree("temp/.git")
except:
    pass


file_names = os.listdir("temp")

for f in file_names: #Coppy files into main dir
    if not f == "puffincoin":
        shutil.copy(os.path.join("temp", f), cwd)
    
file_names_2 = os.listdir("temp/puffincoin")
for f in file_names_2:
    print("COPPYING: " + f)
    shutil.copy(os.path.join("temp/puffincoin", f), os.path.join(cwd, "puffincoin"))

shutil.rmtree("temp")

print("DONE! Updated to latest version.")
