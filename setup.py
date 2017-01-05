from distutils.core import setup
setup(
    name='cesium-grpc',
    packages=['cesium-grpc'],  # this must be the same as the name above
    version='0.1',
    description='a grpc code generator',
    author='chang',
    author_email='zhchang@gmail.com',
    url='https://github.com/zhchang/cesium',  # use the URL to the github repo
    # I'll explain this in a second
    download_url='https://github.com/zhchang/cesium/tarball/0.1',
    keywords=['python', 'grpc', 'code gen'],  # arbitrary keywords
    classifiers=[],
)
