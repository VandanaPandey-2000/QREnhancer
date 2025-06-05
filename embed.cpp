#include <opencv4/opencv2/core.hpp>
#include <opencv2/imgcodecs.hpp>
#include <opencv2/imgproc.hpp>
#include <iostream>
#include <random>

using namespace cv;
using namespace std;

// Function to check safe zones (simplified without ZBar)
bool isSafeZone(const Mat& qrImg, int x, int y, int size, int moduleSize) {
    // QR code structure constants
    int finderPatternSize = 7 * moduleSize;
    int quietZone = 4 * moduleSize;
    
    // Check finder patterns
    if ((x < finderPatternSize + quietZone && y < finderPatternSize + quietZone) ||
        (x > qrImg.cols - finderPatternSize - quietZone && y < finderPatternSize + quietZone) ||
        (x < finderPatternSize + quietZone && y > qrImg.rows - finderPatternSize - quietZone)) {
        return false;
    }
    
    // Check timing patterns
    int timingPos = finderPatternSize + quietZone - moduleSize/2;
    if (abs(y - timingPos) < moduleSize/2 + 1 || abs(x - timingPos) < moduleSize/2 + 1) {
        return false;
    }
    
    // Check bounds
    return !(x + size > qrImg.cols || y + size > qrImg.rows);
}

void blendEdgesWithQR(Mat& qrImg, Mat& embedImg, int x, int y, int moduleSize, int blendPercent ) //int blendPercent added
{
    int borderWidth = moduleSize * 2;
    double scaleAlpha = max(0, min(100, blendPercent)) / 100.0; //edited: this line added
    
    // Sample nearby QR colors
    Scalar topColor = mean(qrImg(Rect(x, max(0,y-1), embedImg.cols, 1)));
    Scalar rightColor = mean(qrImg(Rect(min(qrImg.cols-1,x+embedImg.cols), y, 1, embedImg.rows)));
    Scalar bottomColor = mean(qrImg(Rect(x, min(qrImg.rows-1,y+embedImg.rows), embedImg.cols, 1)));
    Scalar leftColor = mean(qrImg(Rect(max(0,x-1), y, 1, embedImg.rows)));
    
    // Create blend mask
    Mat blendMask = Mat::zeros(embedImg.rows, embedImg.cols, CV_32FC1);
    
    // Horizontal gradients
    for (int i = 0; i < embedImg.rows; i++) {
        float topAlpha = 1.0f - (float)min(i, borderWidth)/borderWidth;
        float bottomAlpha = 1.0f - (float)min(embedImg.rows-1-i, borderWidth)/borderWidth;
        float rowAlpha = max(topAlpha, bottomAlpha);
        
        for (int j = 0; j < embedImg.cols; j++) {
            float leftAlpha = 1.0f - (float)min(j, borderWidth)/borderWidth;
            float rightAlpha = 1.0f - (float)min(embedImg.cols-1-j, borderWidth)/borderWidth;
            blendMask.at<float>(i,j) = max(rowAlpha, max(leftAlpha, rightAlpha));
        }
    }

    // Apply blend percentage scaling
    blendMask *= scaleAlpha;  //eited: this segment added

    
    // Get ROI
    Rect roiRect(x, y, embedImg.cols, embedImg.rows);
    Mat qrROI = qrImg(roiRect);
    
    if (embedImg.channels() == 4) {
        // Process transparent image
        vector<Mat> embedChannels;
        split(embedImg, embedChannels);
        
        Mat alpha;
        embedChannels[3].convertTo(alpha, CV_32FC1, 1.0/255.0);
        multiply(blendMask, alpha, blendMask);  // Combine masks
        
        vector<Mat> qrChannels;
        split(qrROI, qrChannels);
        
        // Create target mats
        Mat targetR(embedImg.size(), CV_32FC1, (topColor[0] + rightColor[0] + bottomColor[0] + leftColor[0])/4);
        Mat targetG(embedImg.size(), CV_32FC1, (topColor[1] + rightColor[1] + bottomColor[1] + leftColor[1])/4);
        Mat targetB(embedImg.size(), CV_32FC1, (topColor[2] + rightColor[2] + bottomColor[2] + leftColor[2])/4);
        
        // Convert channels
        Mat embedR, embedG, embedB;
        embedChannels[0].convertTo(embedR, CV_32FC1);
        embedChannels[1].convertTo(embedG, CV_32FC1);
        embedChannels[2].convertTo(embedB, CV_32FC1);
        
        // Blend operation
        Mat resultR = blendMask.mul(embedR) + (1 - blendMask).mul(targetR);
        Mat resultG = blendMask.mul(embedG) + (1 - blendMask).mul(targetG);
        Mat resultB = blendMask.mul(embedB) + (1 - blendMask).mul(targetB);
        
        // Convert back and merge
        resultR.convertTo(resultR, CV_8UC1);
        resultG.convertTo(resultG, CV_8UC1);
        resultB.convertTo(resultB, CV_8UC1);
        
        vector<Mat> mergedChannels = {resultR, resultG, resultB};
        Mat result;
        merge(mergedChannels, result);
        result.copyTo(qrROI);
    } else {
        // Process opaque image
        Mat embedFloat;
        embedImg.convertTo(embedFloat, CV_32FC3);
        
        // Create target color
        Vec3f targetColor(
            (topColor[0] + rightColor[0] + bottomColor[0] + leftColor[0])/4,
            (topColor[1] + rightColor[1] + bottomColor[1] + leftColor[1])/4,
            (topColor[2] + rightColor[2] + bottomColor[2] + leftColor[2])/4
        );
        
        Mat target(embedImg.size(), CV_32FC3, targetColor);
        
        // Blend operation
        vector<Mat> blendChannels;
        split(blendMask, blendChannels);
        blendChannels.resize(3);  // Duplicate for all channels
        
        Mat blended;
        multiply(embedFloat, blendMask, embedFloat);  // image * mask
        multiply(target, 1 - blendMask, target);      // target * (1-mask)
        add(embedFloat, target, blended);             // combined
        
        blended.convertTo(blended, CV_8UC3);
        blended.copyTo(qrROI);
    }
}

// void embedImage(const string& qrPath, const string& embedPath, const string& outputPath, const string& userRandomData = "") {
void embedImage(const string& qrPath, const string& embedPath, const string& outputPath, const string& userRandomData, int blendPercent){

    // Read images
    Mat qrImg = imread(qrPath, IMREAD_COLOR);
    if (qrImg.empty()) {
        cerr << "Error: Could not read QR code image" << endl;
        return;
    }

    Mat embedImg = imread(embedPath, IMREAD_UNCHANGED);
    if (embedImg.empty()) {
        cerr << "Error: Could not read image to embed" << endl;
        return;
    }

    // Calculate module size (simplified)
    int moduleSize = max(1, qrImg.cols / 21);

    // Resize embed image
    int maxSize = min(qrImg.rows, qrImg.cols) / 3;
    if (embedImg.rows > maxSize || embedImg.cols > maxSize) {
        double ratio = min(static_cast<double>(maxSize) / embedImg.rows, 
                         static_cast<double>(maxSize) / embedImg.cols);
        resize(embedImg, embedImg, Size(), ratio, ratio, INTER_AREA);
    }

    // Find random safe position
    // random_device rd;
    // mt19937 gen(rd());
    
    // Enhanced random seed generation
    random_device rd;
    string combinedSeed = to_string(rd()) + userRandomData;  // Combine both sources
    
    // Create a more complex hash of the combined seed
    size_t seedHash = 0;
    for (char c : combinedSeed) {
        seedHash = (seedHash << 5) + seedHash + c;  // Simple hash mixing
    }
    
    // Initialize random generators with different seeds derived from our hash
    mt19937 genX(seedHash);
    mt19937 genY(seedHash ^ 0x55555555);  // XOR with pattern for different sequence

    uniform_int_distribution<> distX(0, qrImg.cols - embedImg.cols);
    uniform_int_distribution<> distY(0, qrImg.rows - embedImg.rows);

    int x, y;
    int attempts = 0;
    const int maxAttempts = 100;

    do {
        x = distX(genX);
        y = distY(genY);
        attempts++;
    } while (!isSafeZone(qrImg, x, y, embedImg.cols, moduleSize) && attempts < maxAttempts);

    if (attempts >= maxAttempts) {
        cout << "Warning: Could not find optimal position" << endl;
        x = max(0, min(x, qrImg.cols - embedImg.cols));
        y = max(0, min(y, qrImg.rows - embedImg.rows));
    }

    // Blend images with edge matching
     blendEdgesWithQR(qrImg, embedImg, x, y, moduleSize,blendPercent);



    // Save result
    if (!imwrite(outputPath, qrImg)) {
        cerr << "Error: Could not save output image" << endl;
        return;
    }
    cout << "Success: Embedded image saved to " << outputPath << endl;
}

// int main() {
//     cout << "QR Code Image Embedder" << endl;
//     cout << "----------------------" << endl;

//     string qrPath, embedPath, outputPath, userRandomData;
    
//     cout << "Enter QR code image path: ";
//     getline(cin, qrPath);
    
//     cout << "Enter image to embed path: ";
//     getline(cin, embedPath);
    
//     cout << "Enter output path: ";
//     getline(cin, outputPath);

//     cout << "Enter random seed text (optional, press enter to skip): ";
//     getline(cin, userRandomData);

//     // Remove quotes if present
//     auto removeQuotes = [](string& s) {
//         s.erase(remove(s.begin(), s.end(), '\"'), s.end());
//     };
//     removeQuotes(qrPath);
//     removeQuotes(embedPath);
//     removeQuotes(outputPath);

//     embedImage(qrPath, embedPath, outputPath);

//     return 0;
// }

int safe_stoi(const std::string& s, int default_val) {  //edited: added this function
    try {
        return std::stoi(s);
    } catch (...) {
        return default_val;
    }
}

int main(int argc, char** argv) {
    if (argc < 6) {
        cerr << "Usage: " << argv[0] << " <qrPath> <embedPath> <outputPath> <randomSeed> <blendPercent>" << endl;
        return 1;
    }

    string qrPath = argv[1];
    string embedPath = argv[2];
    string outputPath = argv[3];
    string randomSeed = argv[4];
    // int blendPercent = stoi(argv[5]);  //edited: changed a bit
    int blendPercent = safe_stoi(argv[5], 30);  // default 30

    embedImage(qrPath, embedPath, outputPath, randomSeed, blendPercent);
    return 0;
}




