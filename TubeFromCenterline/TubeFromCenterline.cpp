#include <math.h>
#include <fstream>
#include <sstream>
#include <iostream>

#include <vtkActor.h>
#include <vtkCamera.h>
#include <vtkCellArray.h>
#include <vtkDoubleArray.h>
#include <vtkInteractorStyleTrackballCamera.h>
#include <vtkMath.h>
#include <vtkNamedColors.h>
#include <vtkNew.h>
#include <vtkPointData.h>
#include <vtkPoints.h>
#include <vtkPolyData.h>
#include <vtkPolyDataMapper.h>
#include <vtkProperty.h>
#include <vtkRenderWindow.h>
#include <vtkRenderWindowInteractor.h>
#include <vtkRenderer.h>
#include <vtkTubeFilter.h>
#include <vtkUnsignedCharArray.h>
#include <vtkTriangleFilter.h>
#include <vtkSTLWriter.h>

#include <filesystem>
#include <string>
#include <vector>
#include <limits>

// --- Get executable directory (OS dependent) ---
#if defined(_WIN32)
#include <windows.h>
#include <commdlg.h>

static std::filesystem::path GetExeDir()
{
    std::wstring buf(1024, L'\0');
    DWORD len = ::GetModuleFileNameW(nullptr, buf.data(), static_cast<DWORD>(buf.size()));
    if (len >= buf.size())
    {
        buf.resize(len + 1);
        len = ::GetModuleFileNameW(nullptr, buf.data(), static_cast<DWORD>(buf.size()));
    }
    buf.resize(len);
    std::filesystem::path exePath(buf);
    return exePath.parent_path();
}

// Windows: open-file dialog for CSV
static std::filesystem::path OpenCsvFileDialog()
{
    wchar_t szFile[MAX_PATH] = L"";
    OPENFILENAMEW ofn;
    ZeroMemory(&ofn, sizeof(ofn));
    ofn.lStructSize = sizeof(ofn);
    ofn.hwndOwner = nullptr;
    ofn.lpstrFile = szFile;
    ofn.nMaxFile = MAX_PATH;
    ofn.lpstrFilter = L"CSV Files (*.csv)\0*.csv\0All Files (*.*)\0*.*\0";
    ofn.nFilterIndex = 1;

    std::wstring initialDir = GetExeDir().wstring();
    ofn.lpstrInitialDir = initialDir.c_str();

    ofn.Flags = OFN_PATHMUSTEXIST | OFN_FILEMUSTEXIST;

    if (GetOpenFileNameW(&ofn) == TRUE)
    {
        return std::filesystem::path(szFile);
    }
    return std::filesystem::path(); // empty = canceled
}

#elif defined(__APPLE__)
#include <mach-o/dyld.h>

static std::filesystem::path GetExeDir()
{
    uint32_t size = 0;
    _NSGetExecutablePath(nullptr, &size);
    std::vector<char> buf(size);
    if (_NSGetExecutablePath(buf.data(), &size) != 0)
    {
        return std::filesystem::current_path();
    }
    std::filesystem::path exePath = std::filesystem::canonical(std::filesystem::path(buf.data()));
    return exePath.parent_path();
}

// Simple text-based "dialog" for macOS (replace with real GUI if needed)
static std::filesystem::path OpenCsvFileDialog()
{
    std::cout << "Enter CSV file path: " << std::flush;
    std::string path;
    if (!std::getline(std::cin, path))
    {
        return std::filesystem::path();
    }
    if (path.empty())
    {
        return std::filesystem::path();
    }
    return std::filesystem::path(path);
}

#else // Linux/Unix
#include <unistd.h>

static std::filesystem::path GetExeDir()
{
    std::vector<char> buf(1024);
    ssize_t len = ::readlink("/proc/self/exe", buf.data(), buf.size() - 1);
    if (len == -1)
    {
        return std::filesystem::current_path();
    }
    buf[len] = '\0';
    std::filesystem::path exePath = std::filesystem::canonical(std::filesystem::path(buf.data()));
    return exePath.parent_path();
}

// Simple text-based "dialog" for Linux (replace with real GUI if needed)
static std::filesystem::path OpenCsvFileDialog()
{
    std::cout << "Enter CSV file path: " << std::flush;
    std::string path;
    if (!std::getline(std::cin, path))
    {
        return std::filesystem::path();
    }
    if (path.empty())
    {
        return std::filesystem::path();
    }
    return std::filesystem::path(path);
}
#endif

// --- Load centerline points from CSV ---
// 想定フォーマット:
//   ・x,y,z
//   ・または x,y,z,radius
// ヘッダ行があってもOK (数値変換に失敗した行はスキップ)
static bool LoadCenterlineFromCsv(
    const std::filesystem::path &csvPath,
    vtkPoints *points,
    vtkDoubleArray *radiusArray,
    bool &hasRadiusColumn)
{
    hasRadiusColumn = false;

    if (!points || !radiusArray)
    {
        std::cerr << "Null pointer passed to LoadCenterlineFromCsv." << std::endl;
        return false;
    }

    radiusArray->SetName("Radius");
    radiusArray->SetNumberOfComponents(1);
    radiusArray->SetNumberOfTuples(0);

    std::ifstream ifs(csvPath);
    if (!ifs)
    {
        std::cerr << "Failed to open CSV: " << csvPath << std::endl;
        return false;
    }

    std::string line;
    while (std::getline(ifs, line))
    {
        if (line.empty())
        {
            continue;
        }

        std::stringstream ss(line);
        std::string sx, sy, sz, sr;

        // x, y, z は必須
        if (!std::getline(ss, sx, ',')) continue;
        if (!std::getline(ss, sy, ',')) continue;
        if (!std::getline(ss, sz, ',')) continue;

        // 4 列目 (radius) はあってもなくてもよい
        std::getline(ss, sr); // 残り全部

        try
        {
            double x = std::stod(sx);
            double y = std::stod(sy);
            double z = std::stod(sz);
            points->InsertNextPoint(x, y, z);

            // radius 列があれば読んでみる
            if (!sr.empty())
            {
                // sr にさらにカンマが含まれている場合もあるので、先頭トークンだけ使う
                std::stringstream ssr(sr);
                std::string srad;
                if (std::getline(ssr, srad, ','))
                {
                    try
                    {
                        double r = std::stod(srad);
                        radiusArray->InsertNextValue(r);
                    }
                    catch (const std::exception &)
                    {
                        // radius のみ失敗した場合 -> この行の radius は無視
                        // この行の radius が無いと扱う（あとで全体として使用可否をチェック）
                    }
                }
            }
        }
        catch (const std::exception &)
        {
            // x, y, z の変換に失敗した場合 (例: ヘッダ) はスキップ
            continue;
        }
    }

    const vtkIdType nPoints = points->GetNumberOfPoints();
    if (nPoints < 2)
    {
        std::cerr << "Valid point count is less than 2 (not enough for a centerline)." << std::endl;
        return false;
    }

    // radiusArray のタプル数が point 数と完全一致する場合のみ
    // 「radius 列あり」とみなす
    if (radiusArray->GetNumberOfTuples() == nPoints &&
        radiusArray->GetNumberOfTuples() > 0)
    {
        hasRadiusColumn = true;
    }
    else
    {
        if (radiusArray->GetNumberOfTuples() > 0 &&
            radiusArray->GetNumberOfTuples() != nPoints)
        {
            std::cerr << "Warning: radius values exist but count ("
                      << radiusArray->GetNumberOfTuples()
                      << ") != point count (" << nPoints
                      << "). Ignoring radius column." << std::endl;
        }
        radiusArray->Reset();
        hasRadiusColumn = false;
    }

    return true;
}

// --- Ask tube parameters (radius and number of sides) from user ---
// （従来通り：「一様半径」を使う場合にだけ利用）
static bool AskTubeParameters(double &radius, unsigned int &nTv)
{
    std::cout << "=== Tube Parameters (constant radius mode) ===" << std::endl;

    // radius
    std::cout << "Enter tube radius (positive real number, e.g. 0.8): " << std::flush;
    {
        std::string line;
        if (!std::getline(std::cin, line))
        {
            return false;
        }
        std::stringstream ss(line);
        if (!(ss >> radius) || radius <= 0.0)
        {
            std::cerr << "Invalid tube radius." << std::endl;
            return false;
        }
    }

    // number of sides
    std::cout << "Enter number of sides (integer >= 3, e.g. 32): " << std::flush;
    {
        std::string line;
        if (!std::getline(std::cin, line))
        {
            return false;
        }
        unsigned int tmp = 0;
        std::stringstream ss(line);
        if (!(ss >> tmp) || tmp < 3)
        {
            std::cerr << "Invalid number of sides." << std::endl;
            return false;
        }
        nTv = tmp;
    }

    std::cout << "Using tubeRadius = " << radius
              << ", nTv = " << nTv << std::endl
              << std::endl;

    return true;
}

// radius 列がある場合は「側面数」だけを尋ねる
static bool AskNumberOfSides(unsigned int &nTv)
{
    std::cout << "=== Tube Parameters (radius from CSV) ===" << std::endl;
    std::cout << "Radius will be taken from CSV 'radius' column for each point." << std::endl;

    std::cout << "Enter number of sides (integer >= 3, e.g. 32): " << std::flush;
    std::string line;
    if (!std::getline(std::cin, line))
    {
        return false;
    }
    unsigned int tmp = 0;
    {
        std::stringstream ss(line);
        if (!(ss >> tmp) || tmp < 3)
        {
            std::cerr << "Invalid number of sides." << std::endl;
            return false;
        }
        nTv = tmp;
    }

    std::cout << "Using nTv = " << nTv << std::endl << std::endl;
    return true;
}

int main(int, char *[])
{
    vtkNew<vtkNamedColors> nc;

    // 1) Select CSV file via GUI / simple dialog
    std::filesystem::path csvPath = OpenCsvFileDialog();
    if (csvPath.empty())
    {
        std::cerr << "File selection canceled." << std::endl;
        return EXIT_FAILURE;
    }

    // 2) Load centerline points (and optional radius) from CSV
    vtkNew<vtkPoints> points;
    vtkNew<vtkDoubleArray> radiusArray;
    bool hasRadiusColumn = false;

    if (!LoadCenterlineFromCsv(csvPath, points, radiusArray, hasRadiusColumn))
    {
        return EXIT_FAILURE;
    }

    const vtkIdType nV = points->GetNumberOfPoints();
    std::cout << "Loaded point count: " << nV << std::endl;
    if (hasRadiusColumn)
    {
        std::cout << "CSV contains a radius column. Tube radius will vary along the centerline." << std::endl;
    }
    else
    {
        std::cout << "CSV does NOT contain a usable radius column. Using constant radius." << std::endl;
    }

    // 2.5) Ask tube parameters
    double tubeRadius = 0.8;
    unsigned int nTv = 32;

    if (hasRadiusColumn)
    {
        if (!AskNumberOfSides(nTv))
        {
            std::cerr << "Failed to get tube parameters (nTv). Aborting." << std::endl;
            return EXIT_FAILURE;
        }
    }
    else
    {
        if (!AskTubeParameters(tubeRadius, nTv))
        {
            std::cerr << "Failed to get tube parameters. Aborting." << std::endl;
            return EXIT_FAILURE;
        }
    }

    // 3) Build polyline from points
    vtkNew<vtkCellArray> lines;
    lines->InsertNextCell(nV);
    for (vtkIdType i = 0; i < nV; ++i)
    {
        lines->InsertCellPoint(i);
    }

    vtkNew<vtkPolyData> polyData;
    polyData->SetPoints(points);
    polyData->SetLines(lines);

    // 4) Color (blue -> red, visualization only)
    vtkNew<vtkUnsignedCharArray> colors;
    colors->SetName("Colors");
    colors->SetNumberOfComponents(3);
    colors->SetNumberOfTuples(nV);

    for (vtkIdType i = 0; i < nV; ++i)
    {
        double t = (nV > 1) ? static_cast<double>(i) / static_cast<double>(nV - 1) : 0.0;
        unsigned char r = static_cast<unsigned char>(255.0 * t);
        unsigned char b = static_cast<unsigned char>(255.0 * (1.0 - t));
        unsigned char tuple[3] = { r, 0, b };
        colors->SetTypedTuple(i, tuple);
    }

    // 半径列がある場合は point scalars として設定
    if (hasRadiusColumn)
    {
        polyData->GetPointData()->SetScalars(radiusArray);  // active scalars = Radius
    }
    polyData->GetPointData()->AddArray(colors); // Colors はフィールドデータとして追加

    // 5) TubeFilter: constant radius or varying radius
    vtkNew<vtkTubeFilter> tube;
    tube->SetInputData(polyData);
    tube->SetNumberOfSides(static_cast<int>(nTv));

    if (hasRadiusColumn)
    {
        // 各点のスカラー値をそのまま絶対半径として解釈
        tube->SetVaryRadiusToVaryRadiusByAbsoluteScalar();
        // SetRadius() は最小半径の下限として使われるが、
        // 絶対半径モードでは基本的にスカラーがそのまま使われる想定
        std::cout << "Using per-point radius from CSV." << std::endl;
    }
    else
    {
        tube->SetRadius(tubeRadius);
        tube->SetVaryRadiusToVaryRadiusOff();
    }

    // tube->SetCapping(true); // 必要なら端面を閉じる

    // 6) STL output: "output/<csv-filename>_....stl" two levels above exe dir
    std::filesystem::path exeDir = GetExeDir();
    std::filesystem::path outDir = exeDir / ".." / ".." / "output";
    std::error_code ec;
    outDir = std::filesystem::weakly_canonical(outDir, ec);
    std::filesystem::create_directories(outDir, ec);

    std::ostringstream oss;
    oss << csvPath.stem().string();
    if (hasRadiusColumn)
    {
        oss << "_radiusFromCsv";
    }
    else
    {
        oss << "_radius" << tubeRadius;
    }
    oss << "_nTv" << nTv << ".stl";

    std::filesystem::path outFile = outDir / oss.str();

    vtkNew<vtkTriangleFilter> tri;
    tri->SetInputConnection(tube->GetOutputPort());

    vtkNew<vtkSTLWriter> stlWriter;
    stlWriter->SetInputConnection(tri->GetOutputPort());
    const std::string outFileStr = outFile.string();
    stlWriter->SetFileName(outFileStr.c_str());
    // stlWriter->SetFileTypeToASCII(); // Uncomment if you prefer ASCII STL
    stlWriter->Write();

    std::cout << "STL saved to: " << outFileStr << std::endl;

    // 7) Visualization
    vtkNew<vtkPolyDataMapper> mapper;
    mapper->SetInputConnection(tube->GetOutputPort());
    mapper->ScalarVisibilityOn();
    mapper->SetScalarModeToUsePointFieldData();
    mapper->SelectColorArray("Colors");  // 色は Colors 配列から

    vtkNew<vtkActor> actor;
    actor->SetMapper(mapper);

    vtkNew<vtkRenderer> renderer;
    renderer->AddActor(actor);
    renderer->SetBackground(nc->GetColor3d("SteelBlue").GetData());

    renderer->GetActiveCamera()->Azimuth(30);
    renderer->GetActiveCamera()->Elevation(30);
    renderer->ResetCamera();

    vtkNew<vtkRenderWindow> renWin;
    vtkNew<vtkRenderWindowInteractor> iren;
    iren->SetRenderWindow(renWin);
    renWin->AddRenderer(renderer);
    renWin->SetSize(500, 500);
    renWin->SetWindowName("TubeFromCenterline (CSV, radius from CSV or constant)");
    renWin->Render();

    vtkNew<vtkInteractorStyleTrackballCamera> style;
    iren->SetInteractorStyle(style);
    iren->Start();

    return EXIT_SUCCESS;
}
