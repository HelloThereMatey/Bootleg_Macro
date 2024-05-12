import subprocess
import json
from pprint import pprint
import re
import os

wd = os.path.dirname(os.path.abspath(__file__))
fdel = os.path.sep

def js_search_tv(searchstr: str) -> dict:
    data_str = json.dumps(searchstr)

    # Run Node.js process and pass data
    #result = subprocess.run(['node', 'pyinout.js'], input=data, text=True, capture_output=True).stdout.replace('\n', '').replace("'", "")
    result = subprocess.run(['node', wd+fdel+'searchTV_js.js'], input=data_str, text=True, capture_output=True)
    print("Return code:", result.returncode)

    if result.returncode != 0:
        print("Error:", result.stderr)
        quit()
    else:
        print("Output:", result.stdout.replace('\n', '').replace("'", ""))
        response = result.stdout.replace('\n', '').replace("'", "")

    returned = response[2::].split("{    ")

    full_dict = {}; j = 0
    for st in returned:
        split2 = st.split(",")
        i = 0
        outdict = {}
        for st2 in split2:
            if i == 0:
                text = st2
                # Using re.sub to remove the middle part between two colons
                modified_text = re.sub(r'([^:]*):[^:]*(:.*)', r'\1\2', text)
                st2 = modified_text.replace("}", "")
            i += 1
            line = st2.replace("}", "").strip()
            els = line.split(":")
            try:
                outdict[els[0]] = els[1]
            except:
                pass
        full_dict[j] = outdict
        j += 1
    del full_dict[0]    
    return full_dict

if __name__ == "__main__":

    searchstr = "MSTR"
    print("Searching trading view data for:", searchstr)
    
    #Convert Python dictionary to JSON string
    pprint(js_search_tv(searchstr))
