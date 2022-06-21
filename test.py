file_path = input("Enter File Path:")
a=input("Enter For filter Data: ")
ss = open(file_path,"r")
for l in ss:
    if a in l:
        print(l)