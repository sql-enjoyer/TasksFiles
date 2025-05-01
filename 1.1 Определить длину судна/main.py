import cv2
import numpy as np
import glob
import pickle
import os
import argparse

class DistortionCorrector:
    def __init__(self):
        self.mtx = None
        self.dist = None
        self.new_mtx = None
        self.roi = None
        self.calibrated = False
        self.rms = None

    def calibrate(self, pattern_path, chessboard_size=(9,6), save_file='calibration_data.pkl'):
        objp = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
        objp[:, :2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2)

        objpoints = []
        imgpoints = []
        images = glob.glob(pattern_path)

        if not images:
            raise FileNotFoundError(f"No images found at {pattern_path}")

        for fname in images:
            img = cv2.imread(fname)
            if img is None:
                continue

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, chessboard_size, None)

            if ret:
                objpoints.append(objp)
                corners_refined = cv2.cornerSubPix(
                    gray, corners, (11,11), (-1,-1),
                    criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
                )
                imgpoints.append(corners_refined)

        if not objpoints:
            raise ValueError("Chessboard corners not found in any images")
        
        rms, self.mtx, self.dist, rvecs, tvecs = cv2.calibrateCamera(
            objpoints, imgpoints, gray.shape[::-1], None, None
        )

        self._save_calibration(save_file, rms)
        self.calibrated = True
        self.rms = rms
        print(f"Calibration successful! RMS: {rms:.4f} pixels")
        print(f"Matrix:\n{self.mtx}")
        print(f"Distortion coefficients:\n{self.dist}")

    def _save_calibration(self, filename, rms):
        data = {
            'mtx': self.mtx,
            'dist': self.dist,
            'rms': rms
        }
        with open(filename, 'wb') as f:
            pickle.dump(data, f)

    def load_calibration(self, filename):
        with open(filename, 'rb') as f:
            data = pickle.load(f)
        self.mtx = data['mtx']
        self.dist = data['dist']
        self.rms = data.get('rms', None)
        self.calibrated = True
        print(f"Loaded calibration with RMS: {self.rms:.4f} pixels")

    # Остальные методы без изменений
    def correct_image(self, img, crop=True):
        if not self.calibrated:
            raise RuntimeError("Corrector not calibrated")

        h, w = img.shape[:2]
        self.new_mtx, self.roi = cv2.getOptimalNewCameraMatrix(
            self.mtx, self.dist, (w,h), 1, (w,h))
        dst = cv2.undistort(img, self.mtx, self.dist, None, self.new_mtx)
        
        if crop and self.roi is not None:
            x,y,w,h = self.roi
            return dst[y:y+h, x:x+w]
        return dst

    def correct_images(self, input_path, output_folder, crop=True):
        os.makedirs(output_folder, exist_ok=True)
        images = glob.glob(input_path)
        
        for fname in images:
            img = cv2.imread(fname)
            if img is None:
                continue

            dst = self.correct_image(img, crop)
            out_path = os.path.join(output_folder, os.path.basename(fname))
            cv2.imwrite(out_path, dst)
            print(f"Corrected image saved to {out_path}")

def main():
    parser = argparse.ArgumentParser(description='Camera Distortion Correction Tool')
    subparsers = parser.add_subparsers(dest='command')

    calibrate_parser = subparsers.add_parser('calibrate', help='Calibrate camera using chessboard pattern')
    calibrate_parser.add_argument('--pattern_path', required=True, 
                                help='Path to calibration images (e.g. "calib_images/*.jpg")')
    calibrate_parser.add_argument('--chessboard_size', type=int, nargs=2, default=[9,6],
                                help='Number of inner corners (width, height)')
    calibrate_parser.add_argument('--output_file', default='calibration_data.pkl',
                                help='Output calibration file name')

    correct_parser = subparsers.add_parser('correct', help='Correct distortion in images')
    correct_parser.add_argument('--input', required=True,
                              help='Input images path (e.g. "images/*.jpg")')
    correct_parser.add_argument('--output_dir', default='corrected',
                              help='Output directory for corrected images')
    correct_parser.add_argument('--calibration', required=True,
                              help='Calibration file path')

    realtime_parser = subparsers.add_parser('realtime', help='Real-time distortion correction')
    realtime_parser.add_argument('--calibration', required=True,
                               help='Calibration file path')
    realtime_parser.add_argument('--camera', type=int, default=0,
                               help='Camera device ID')

    args = parser.parse_args()
    corrector = DistortionCorrector()

    try:
        if args.command == 'calibrate':
            corrector.calibrate(
                pattern_path=args.pattern_path,
                chessboard_size=tuple(args.chessboard_size),
                save_file=args.output_file
            )
        
        elif args.command == 'correct':
            corrector.load_calibration(args.calibration)
            corrector.correct_images(args.input, args.output_dir)
        
        elif args.command == 'realtime':
            corrector.load_calibration(args.calibration)
            cap = cv2.VideoCapture(args.camera)
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                dst = corrector.correct_image(frame, crop=False)
                cv2.imshow('Original', frame)
                cv2.imshow('Corrected', dst)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            cap.release()
            cv2.destroyAllWindows()
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()