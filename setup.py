from distutils.core import setup
ver = '0.93'
setup(
    name='cesium_grpc',
    packages=['cesium_grpc'],  # this must be the same as the name above
    version=ver,
    description='a grpc code generator',
    author='chang',
    author_email='zhchang@gmail.com',
    url='https://github.com/zhchang/cesium',  # use the URL to the github repo
    # I'll explain this in a second
    download_url='https://github.com/zhchang/cesium/tarball/' + ver,
    keywords=['python', 'grpc', 'code gen'],  # arbitrary keywords
    scripts=['scripts/add_wrapper'],
    classifiers=[],
)
