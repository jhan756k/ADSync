import pickle

filename = "f.txt"
file = open(filename, "rb")
data = pickle.load(file)
file.close()
print(data)