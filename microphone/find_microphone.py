import pyaudio

# load in our audio recording device
p = pyaudio.PyAudio()
print('DEFAULT MICROPHONE DEVICE')
print('=========================')
print(p.get_default_input_device_info())

print("")
print("ALL MICROPHONE DEVICES")
print('=========================')
for i in range(p.get_device_count()):
    print(p.get_device_info_by_index(i))


print("")
print("IF THE MICROPHONE YOU WANT IS NOT THE DEFAULT, MAKE SURE")
print("YOU SPECIFY THIS IN THE CODE LATER.")
