# -*- coding: utf-8 -*-

import os
import pytest
import shutil
import tifftools

from large_image import constants
import large_image_source_tiff

import large_image_converter
import large_image_converter.__main__ as main

from . import utilities


def testIsGeospatial():
    testDir = os.path.dirname(os.path.realpath(__file__))
    imagePath = os.path.join(testDir, 'test_files', 'rgb_geotiff.tiff')
    assert large_image_converter.is_geospatial(imagePath) is True

    imagePath = utilities.externaldata(
        'data/sample_svs_image.TCGA-DU-6399-01A-01-TS1.e8eb65de-d63e-42db-'
        'af6f-14fefbbdf7bd.svs.sha512')
    assert large_image_converter.is_geospatial(imagePath) is False

    testDir = os.path.dirname(os.path.realpath(__file__))
    imagePath = os.path.join(testDir, 'test_files', 'yb10kx5k.png')
    assert large_image_converter.is_geospatial(imagePath) is False


def testIsVips():
    imagePath = utilities.externaldata(
        'data/sample_svs_image.TCGA-DU-6399-01A-01-TS1.e8eb65de-d63e-42db-'
        'af6f-14fefbbdf7bd.svs.sha512')
    assert large_image_converter.is_vips(imagePath) is True

    imagePath = utilities.externaldata('data/HENormalN801.czi.sha512')
    assert large_image_converter.is_vips(imagePath) is False


@pytest.mark.parametrize('convert_args,taglist', [
    ({}, {
        tifftools.Tag.Compression.value: tifftools.constants.Compression.LZW.value,
        tifftools.Tag.TileWidth.value: 256
    }),
    ({'compression': 'jpeg'}, {
        tifftools.Tag.Compression.value: tifftools.constants.Compression.JPEG.value
    }),
    ({'compression': 'deflate'}, {
        tifftools.Tag.Compression.value: tifftools.constants.Compression.AdobeDeflate.value
    }),
    ({'compression': 'lzw'}, {
        tifftools.Tag.Compression.value: tifftools.constants.Compression.LZW.value
    }),
    ({'compression': 'packbits'}, {
        tifftools.Tag.Compression.value: tifftools.constants.Compression.Packbits.value
    }),
    ({'compression': 'zstd'}, {
        tifftools.Tag.Compression.value: tifftools.constants.Compression.ZSTD.value
    }),
    ({'compression': 'jpeg', 'quality': 50}, {
        tifftools.Tag.Compression.value: tifftools.constants.Compression.JPEG.value
    }),
    ({'compression': 'deflate', 'level': 2}, {
        tifftools.Tag.Compression.value: tifftools.constants.Compression.AdobeDeflate.value
    }),
    ({'compression': 'lzw', 'predictor': 'yes'}, {
        tifftools.Tag.Compression.value: tifftools.constants.Compression.LZW.value
    }),
    ({'compression': 'webp', 'quality': 0}, {
        tifftools.Tag.Compression.value: tifftools.constants.Compression.WEBP.value
    }),
    ({'tileSize': 512}, {
        tifftools.Tag.TileWidth.value: 512
    }),
])
def testConvert(tmpdir, convert_args, taglist):
    testDir = os.path.dirname(os.path.realpath(__file__))
    imagePath = os.path.join(testDir, 'test_files', 'yb10kx5k.png')
    outputPath = os.path.join(tmpdir, 'out.tiff')
    large_image_converter.convert(imagePath, outputPath, **convert_args)
    info = tifftools.read_tiff(outputPath)
    for key, value in taglist.items():
        assert info['ifds'][0]['tags'][key]['data'][0] == value


def testConvertGeospatial(tmpdir):
    testDir = os.path.dirname(os.path.realpath(__file__))
    imagePath = os.path.join(testDir, 'test_files', 'rgb_geotiff.tiff')
    inputPath = os.path.join(tmpdir, 'in.geo.tiff')
    shutil.copy(imagePath, inputPath)
    outputPath = large_image_converter.convert(inputPath, level=5)
    assert 'geo.tiff' in outputPath
    assert outputPath != inputPath
    info = tifftools.read_tiff(outputPath)
    assert tifftools.Tag.ModelTiepointTag.value in info['ifds'][0]['tags']


def testConvertPTIF(tmpdir):
    imagePath = utilities.externaldata('data/sample_image.ptif.sha512')
    outputPath = os.path.join(tmpdir, 'out.tiff')
    large_image_converter.convert(imagePath, outputPath, compression='jpeg', quality=50)
    info = tifftools.read_tiff(outputPath)
    assert len(info['ifds']) == 11


def testConvertOverwrite(tmpdir):
    testDir = os.path.dirname(os.path.realpath(__file__))
    imagePath = os.path.join(testDir, 'test_files', 'yb10kx5k.png')
    outputPath = os.path.join(tmpdir, 'out.tiff')
    open(outputPath, 'w').write('placeholder')
    with pytest.raises(Exception):
        large_image_converter.convert(imagePath, outputPath)
    large_image_converter.convert(imagePath, outputPath, overwrite=True)
    assert os.path.getsize(outputPath) > 100


def testConvertOMETif(tmpdir):
    imagePath = utilities.externaldata('data/sample.ome.tif.sha512')
    outputPath = os.path.join(tmpdir, 'out.tiff')
    # Note: change this when we convert multi-frame files differently
    large_image_converter.convert(imagePath, outputPath)
    info = tifftools.read_tiff(outputPath)
    assert len(info['ifds']) == 3
    assert len(info['ifds'][0]['tags'][tifftools.Tag.SubIFD.value]['ifds']) == 4


def testConvertTiffFloatPixels(tmpdir):
    imagePath = utilities.externaldata('data/d042-353.crop.small.float32.tif.sha512')
    outputPath = os.path.join(tmpdir, 'out.tiff')
    large_image_converter.convert(imagePath, outputPath)
    info = tifftools.read_tiff(outputPath)
    assert (info['ifds'][0]['tags'][tifftools.Tag.SampleFormat.value]['data'][0] ==
            tifftools.constants.SampleFormat.uint.value)


def testConvertJp2kCompression(tmpdir):
    imagePath = utilities.externaldata('data/sample_Easy1.png.sha512')
    outputPath = os.path.join(tmpdir, 'out.tiff')
    large_image_converter.convert(imagePath, outputPath, compression='jp2k')
    info = tifftools.read_tiff(outputPath)
    assert (info['ifds'][0]['tags'][tifftools.Tag.Compression.value]['data'][0] ==
            tifftools.constants.Compression.JP2000.value)
    source = large_image_source_tiff.TiffFileTileSource(outputPath)
    image, _ = source.getRegion(
        output={'maxWidth': 200, 'maxHeight': 200}, format=constants.TILE_FORMAT_NUMPY)
    assert (image[12][167] == [215, 135, 172]).all()

    outputPath2 = os.path.join(tmpdir, 'out2.tiff')
    large_image_converter.convert(imagePath, outputPath2, compression='jp2k', psnr=50)
    assert os.path.getsize(outputPath2) < os.path.getsize(outputPath)

    outputPath3 = os.path.join(tmpdir, 'out3.tiff')
    large_image_converter.convert(imagePath, outputPath3, compression='jp2k', cr=100)
    assert os.path.getsize(outputPath3) < os.path.getsize(outputPath)
    assert os.path.getsize(outputPath3) != os.path.getsize(outputPath2)


def testConvertFromLargeImage(tmpdir):
    imagePath = utilities.externaldata('data/sample_image.jp2.sha512')
    outputPath = os.path.join(tmpdir, 'out.tiff')
    large_image_converter.convert(imagePath, outputPath)
    source = large_image_source_tiff.TiffFileTileSource(outputPath)
    metadata = source.getMetadata()
    assert metadata['levels'] == 6


def testConverterMain(tmpdir):
    testDir = os.path.dirname(os.path.realpath(__file__))
    imagePath = os.path.join(testDir, 'test_files', 'yb10kx5k.png')
    outputPath = os.path.join(tmpdir, 'out.tiff')
    main.main([imagePath, outputPath])
    assert os.path.getsize(outputPath) > 100

    outputPath2 = os.path.join(tmpdir, 'out2.tiff')
    main.main([imagePath, outputPath2, '--compression', 'zip'])
    assert os.path.getsize(outputPath2) > 100
    assert os.path.getsize(outputPath2) < os.path.getsize(outputPath)


def testConverterMainNonFile(tmpdir):
    outputPath = os.path.join(tmpdir, 'out.tiff')
    assert main.main(['not a file', outputPath]) == 1


def testConverterMainNonImageFile(tmpdir):
    testDir = os.path.dirname(os.path.realpath(__file__))
    imagePath = os.path.join(testDir, 'test_files', 'notanimage.txt')
    outputPath = os.path.join(tmpdir, 'out.tiff')
    with pytest.raises(Exception):
        main.main([imagePath, outputPath])
    assert not os.path.exists(outputPath)
