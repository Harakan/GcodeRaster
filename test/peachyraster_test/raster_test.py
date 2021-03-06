import unittest
import logging
from mock import patch, mock_open, call
import os
import os.path
import sys
from PIL import Image
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from peachyraster.raster import Raster, ImageRaster

@patch('peachyraster.raster.ImageRaster')
class RasterTest(unittest.TestCase):

    def test_init_file_should_setup_image_raster_with_defaults(self, mockImageRaster):
        Raster()
        mockImageRaster.assert_called_with(0.5, True, back_and_forth=False)

    @patch.object(os.path, 'isfile')
    @patch.object(Image, 'open')
    def test_process_file_should_call_image_raster_when_file_exists(self, mock_imread, mock_isfile, mockImageRaster):
        mock_isfile.return_value = True
        mock_imread.return_value = "SomeArray"
        mock_file_raster = mockImageRaster.return_value
        with patch('peachyraster.raster.open', mock_open(), create=True):
            rasterer = Raster()
            rasterer.process_file("test0.png")
        mock_file_raster.process.assert_called_with('SomeArray', 0.0)

    @patch.object(os.path, 'isfile')
    @patch.object(Image, 'open')
    @patch.object(os, 'listdir')
    def test_process_folder_should_call_image_raster_for_each_image_file(self, mock_list_dir, mock_imread, mock_isfile, mockImageRaster):
        mock_isfile.return_value = True
        mock_imread.return_value = "SomeArray"
        mock_list_dir.return_value = ['1.jpg', '2.png', "3.txt"]
        mock_file_raster = mockImageRaster.return_value
        with patch('peachyraster.raster.open', mock_open(), create=True):
            rasterer = Raster( layer_height=1.0)
            rasterer.process_folder("test")
        self.assertEquals( [call(os.path.join('test','1.jpg')), call(os.path.join('test','2.png'))] , mock_imread.call_args_list)
        self.assertEquals(2, mock_file_raster.process.call_count)
        self.assertEquals(call("SomeArray", 0.0) , mock_file_raster.process.call_args_list[0])
        self.assertEquals(call("SomeArray", 1.0) , mock_file_raster.process.call_args_list[1])

    @patch.object(os.path, 'isfile')
    @patch.object(Image, 'open')
    @patch.object(os, 'listdir')
    def test_process_folder_should_sort_images(self, mock_list_dir, mock_imread, mock_isfile, mockImageRaster):
        mock_isfile.return_value = True
        mock_imread.return_value = "SomeArray"
        mock_list_dir.return_value = ['b.jpg', 'a.png', "d.jpeg"]
        with patch('peachyraster.raster.open', mock_open(), create=True):
            rasterer = Raster( layer_height=1.0)
            rasterer.process_folder("test")
        self.assertEquals( [
            call(os.path.join('test','a.png')), 
            call(os.path.join('test','b.jpg')),
            call(os.path.join('test','d.jpeg')),
            ], mock_imread.call_args_list)


    @patch.object(os.path, 'isfile')
    @patch.object(Image, 'open')
    def test_process_file_should_write_output_to_file(self, mock_imread, mock_isfile, mockImageRaster):
        output_file = 'out.gcode'
        output_data = "some_gcode"
        mock_isfile.return_value = True
        mock_imread.return_value = "SomeArray"
        mock_file_raster = mockImageRaster.return_value
        mock_file_raster.process.return_value = output_data
        mocked_open = mock_open()

        with patch('peachyraster.raster.open', mocked_open, create=True):
            rasterer = Raster(output_file_name=output_file)
            rasterer.process_file("test0.png")
            mocked_open.assert_called_with(output_file, 'w')
            mocked_open.return_value.write.assert_called_with(output_data)
        mock_file_raster.process.assert_called_with('SomeArray', 0.0)

    @patch.object(os.path, 'isfile')
    @patch.object(Image, 'open')
    def test_process_file_should_write_output_to_file_if_no_name_provided(self, mock_imread, mock_isfile, mockImageRaster):
        output_data = "some_gcode"
        mock_isfile.return_value = True
        mock_imread.return_value = "SomeArray"
        mock_file_raster = mockImageRaster.return_value
        mock_file_raster.process.return_value = output_data
        mocked_open = mock_open()

        with patch('peachyraster.raster.open', mocked_open, create=True):
            rasterer = Raster()
            rasterer.process_file("test0.png")
            self.assertEquals('w', mocked_open.call_args[0][1])
            self.assertTrue(mocked_open.call_args[0][0].startswith('out'))
            mocked_open.return_value.write.assert_called(output_data)
        mock_file_raster.process.assert_called_with('SomeArray', 0.0)

    def test_process_file_should_not_call_file_raster_when_file_does_not_exists(self, mockImageRaster):
        mock_file_raster = mockImageRaster.return_value
        with patch('peachyraster.raster.open', mock_open(), create=True):
            rasterer = Raster()
            with self.assertRaises(IOError):
                rasterer.process_file("test1.png")
        self.assertEquals(0, mock_file_raster.process.call_count)


class ImageRasterTest(unittest.TestCase):
    def print_ascii(self, image):
        string = ''
        for x in range(0, image.shape[0]):
            for y in range(0, image.shape[1]):
                if np.array_equal(image[x][y], [0, 0, 0]):
                    string += '$'
                else:
                    string += ' '
            string += '\n'
        print(string + '\n-------\n')

    def test_process_should_return_gcode_for_rectangle_image_with_borders(self):
        laser_width = 1
        image = np.array([[[0, 0, 0],[255, 255, 255]],
                          [[0, 0, 0],[255, 255, 255]],
                          [[255, 255, 255],[0, 0, 0]]], dtype=np.uint8)
        # @@@@
        # @@ @
        # @@ @
        # @ @@
        # @@@@
        expected_gcode = "".join([
        "G1 Z0.00 F1\n",
        "G0 F1 X-1.50 Y2.00 E0.00\n",
        "G1 F1 X1.50 Y2.00 E4.00\n",
        "G0 F1 X-1.50 Y1.00 E0.00\n",
        "G1 F1 X-0.50 Y1.00 E6.00\n",
        "G0 F1 X1.50 Y1.00 E0.00\n",
        "G1 F1 X1.50 Y1.00 E7.00\n",
        "G0 F1 X-1.50 Y0.00 E0.00\n",
        "G1 F1 X-0.50 Y0.00 E9.00\n",
        "G0 F1 X1.50 Y0.00 E0.00\n",
        "G1 F1 X1.50 Y0.00 E10.00\n",
        "G0 F1 X-1.50 Y-1.00 E0.00\n",
        "G1 F1 X-1.50 Y-1.00 E11.00\n",
        "G0 F1 X0.50 Y-1.00 E0.00\n",
        "G1 F1 X1.50 Y-1.00 E13.00\n",
        "G0 F1 X-1.50 Y-2.00 E0.00\n",
        "G1 F1 X1.50 Y-2.00 E17.00\n",])

        IR = ImageRaster(laser_width, True)
        result = IR.process(image)
        self.assertEquals(expected_gcode, result, self.gcode_equal(expected_gcode, result))

    def test_process_should_return_gcode_at_specified_height(self):
        laser_width = 1
        height = 1.2
        image = np.array([[[0, 0, 0],[255, 255, 255]],
                          [[0, 0, 0],[255, 255, 255]],
                          [[255, 255, 255],[0, 0, 0]]], dtype=np.uint8)
        # @@@@
        # @@ @
        # @@ @
        # @ @@
        # @@@@
        expected_gcode = "".join([
        "G1 Z1.20 F1\n",
        "G0 F1 X-1.50 Y2.00 E0.00\n",
        "G1 F1 X1.50 Y2.00 E4.00\n",
        "G0 F1 X-1.50 Y1.00 E0.00\n",
        "G1 F1 X-0.50 Y1.00 E6.00\n",
        "G0 F1 X1.50 Y1.00 E0.00\n",
        "G1 F1 X1.50 Y1.00 E7.00\n",
        "G0 F1 X-1.50 Y0.00 E0.00\n",
        "G1 F1 X-0.50 Y0.00 E9.00\n",
        "G0 F1 X1.50 Y0.00 E0.00\n",
        "G1 F1 X1.50 Y0.00 E10.00\n",
        "G0 F1 X-1.50 Y-1.00 E0.00\n",
        "G1 F1 X-1.50 Y-1.00 E11.00\n",
        "G0 F1 X0.50 Y-1.00 E0.00\n",
        "G1 F1 X1.50 Y-1.00 E13.00\n",
        "G0 F1 X-1.50 Y-2.00 E0.00\n",
        "G1 F1 X1.50 Y-2.00 E17.00\n",])

        IR = ImageRaster(laser_width, True)
        result = IR.process(image, height)
        self.assertEquals(expected_gcode, result, self.gcode_equal(expected_gcode, result))

    def test_process_should_return_gcode_with_no_borders(self):
        laser_width = 1
        height = 1.2
        borders = 0
        image = np.array([[[0, 0, 0],[255, 255, 255]],
                          [[0, 0, 0],[255, 255, 255]],
                          [[255, 255, 255],[0, 0, 0]]], dtype=np.uint8)
        # @ 
        # @ 
        #  @
        expected_gcode = "".join([
        "G1 Z1.20 F1\n",
        "G0 F1 X-0.50 Y1.00 E0.00\n",
        "G1 F1 X-0.50 Y1.00 E1.00\n",
        "G0 F1 X-0.50 Y0.00 E0.00\n",
        "G1 F1 X-0.50 Y0.00 E2.00\n",
        "G0 F1 X0.50 Y-1.00 E0.00\n",
        "G1 F1 X0.50 Y-1.00 E3.00\n",])

        IR = ImageRaster(laser_width, borders)
        result = IR.process(image, height)
        self.assertEquals(expected_gcode, result, self.gcode_equal(expected_gcode, result))

    def test_process_should_return_gcode_with_specified_border(self):
        laser_width = 1
        height = 1.2
        border = 2
        image = np.array([[[0, 0, 0],[255, 255, 255]],
                          [[0, 0, 0],[255, 255, 255]],
                          [[255, 255, 255],[0, 0, 0]]], dtype=np.uint8)
        # @@@@@@
        # @@@@@@
        # @@@ @@
        # @@@ @@
        # @@ @@@
        # @@@@@@
        # @@@@@@
        expected_gcode = "".join([
        "G1 Z1.20 F1\n",
        "G0 F1 X-2.50 Y3.00 E0.00\n",
        "G1 F1 X2.50 Y3.00 E6.00\n",
        "G0 F1 X-2.50 Y2.00 E0.00\n",
        "G1 F1 X2.50 Y2.00 E12.00\n",
        "G0 F1 X-2.50 Y1.00 E0.00\n",
        "G1 F1 X-0.50 Y1.00 E15.00\n",
        "G0 F1 X1.50 Y1.00 E0.00\n",
        "G1 F1 X2.50 Y1.00 E17.00\n",
        "G0 F1 X-2.50 Y0.00 E0.00\n",
        "G1 F1 X-0.50 Y0.00 E20.00\n",
        "G0 F1 X1.50 Y0.00 E0.00\n",
        "G1 F1 X2.50 Y0.00 E22.00\n",
        "G0 F1 X-2.50 Y-1.00 E0.00\n",
        "G1 F1 X-1.50 Y-1.00 E24.00\n",
        "G0 F1 X0.50 Y-1.00 E0.00\n",
        "G1 F1 X2.50 Y-1.00 E27.00\n",
        "G0 F1 X-2.50 Y-2.00 E0.00\n",
        "G1 F1 X2.50 Y-2.00 E33.00\n",
        "G0 F1 X-2.50 Y-3.00 E0.00\n",
        "G1 F1 X2.50 Y-3.00 E39.00\n",])

        IR = ImageRaster(laser_width, border)
        result = IR.process(image, height)
        self.assertEquals(expected_gcode, result, self.gcode_equal(expected_gcode, result))

    def test_process_should_do_back_and_forth_rasters(self):
        laser_width = 1
        height = 1.2
        image = np.array([[[0, 0, 0],[255, 255, 255]],
                          [[0, 0, 0],[255, 255, 255]],
                          [[255, 255, 255],[0, 0, 0]]], dtype=np.uint8)
        # @@@@
        # @@ @
        # @@ @
        # @ @@
        # @@@@
        expected_gcode = "".join([
        "G1 Z1.20 F1\n",
        "G0 F1 X-1.50 Y2.00 E0.00\n",
        "G1 F1 X1.50 Y2.00 E4.00\n",

        "G0 F1 X1.50 Y1.00 E0.00\n",
        "G1 F1 X1.50 Y1.00 E5.00\n",
        "G0 F1 X-0.50 Y1.00 E0.00\n",
        "G1 F1 X-1.50 Y1.00 E7.00\n",

        "G0 F1 X-1.50 Y0.00 E0.00\n",
        "G1 F1 X-0.50 Y0.00 E9.00\n",
        "G0 F1 X1.50 Y0.00 E0.00\n",
        "G1 F1 X1.50 Y0.00 E10.00\n",

        "G0 F1 X1.50 Y-1.00 E0.00\n",
        "G1 F1 X0.50 Y-1.00 E12.00\n",
        "G0 F1 X-1.50 Y-1.00 E0.00\n",
        "G1 F1 X-1.50 Y-1.00 E13.00\n",

        "G0 F1 X-1.50 Y-2.00 E0.00\n",
        "G1 F1 X1.50 Y-2.00 E17.00\n",])

        IR = ImageRaster(laser_width, True, back_and_forth=True)
        result = IR.process(image, height)
        self.assertEquals(expected_gcode, result, self.gcode_equal(expected_gcode, result))

    def gcode_equal(self, one, two):
        result = '\n'
        one = one.split('\n')
        two = two.split('\n')
        for i in range(0, max(len(one), len(two)) - 1):
            p1 = one[i] if i < len(one) else ''
            p2 = two[i] if i < len(two) else ''
            if p1 == p2:
                result += "{:40} ==== {:40}\n".format(p1, p2)
            else:
                result += "{:40} !!!! {:40}\n".format(p1, p2)
        return result

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level='DEBUG')
    unittest.main()
