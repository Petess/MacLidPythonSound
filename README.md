# MacLidPythonSound
This code generates a tone that changes with the angle of the Mac screen

It was inspired by this : 

https://news.ycombinator.com/item?id=45158968

And the code here. 

https://github.com/samhenrigold/LidAngleSensor

This reads the sensors using the 'pybooklid' library and uses pygame to generate a tone and show instructions 

## Tested platforms

This has been tested on a Macbook Air M4 

## Requirements 

A Mac that can work with the 'pybooklid' library. 

You can check if your Mac can read the sensor with the following script 

https://gist.github.com/samhenrigold/42b5a92d1ee8aaf2b840be34bff28591

The following needs to be installed via uv or pip :

pygame numpy sounddevice pybooklid

## Notes

Claude AI was used to develop this with some documentation. 
