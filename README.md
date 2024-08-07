<div align="center">
    
# RealSense Data Processing System

本項目應用範圍涵蓋從感測器的數據獲取、數據處理到生成網格，用戶可以通過深度感測器在本項目的 Record 模式上獲取 RGBD 數據或是在 View 模式上獲取點雲，RGBD 數據可以使用本項目的 RunSystem 模式，把數據直接處理成 mesh 網格，適合用於重建三維場景的重建，單個物體的情況可以使用 View 模式下的功能來獲取點雲，除了獲取數據， View 模式還包括取多功能，點雲 手/自動 配準、點雲處理、點雲轉網格、網格轉點雲、降採樣、點雲可視化。

<div align="left">

## 環境配置

以下指令需在 Python 版本等於 3.10 的環境下進行

### 本項目目前只在 Windows 10/11 環境下進行測試
#### 通過 pip 安裝依賴 
```bash
pip install -r requirements.txt
```

## 使用說明

### 直接啟動
1. 進入 `src` 資料夾：
    ```bash
    cd src
    ```
    
2. 運行主程序：
    ```bash
    python main.py
    ```
### 使用整合包
1. 下載並解壓縮 `STUSTcloudproject.zip`
2. 雙擊 `run.bat`

## 詳細文檔

有關詳細的項目目錄結構和介紹，請參閱 [docs/directory_structure.md](docs/directory_structure.md)。
