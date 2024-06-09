# RealSense Data Processing System

## 簡介

此項目旨在提供一個基於 RealSense 的數據處理系統，包括數據錄製、數據處理和數據視圖顯示功能。系統使用 MVC 架構進行設計和實現，並提供了豐富的自定義小部件以提升用戶體驗。

## 目錄

- [安裝和配置](#安裝和配置)
- [使用說明](#使用說明)
- [貢獻指南](#貢獻指南)
- [版權和許可](#版權和許可)
- [詳細文檔](#詳細文檔)

## 安裝和配置

### 前置條件

請確保已安裝以下軟件：
- Python 3.7 或更高版本
- pip

### 安裝步驟

1. 克隆此存儲庫到本地：
    ```bash
    git clone https://github.com/your_username/your_repository.git
    ```

2. 進入項目目錄並安裝所需依賴：
    ```bash
    cd your_repository
    pip install -r requirements.txt
    ```

3. 配置項目：
    - 編輯 `config.json` 和 `realsense.json` 文件以適應你的需求

## 使用說明

1. 運行主程序：
    ```bash
    python main.py
    ```

2. 使用 GUI 進行操作：
    - `Home`：查看應用說明
    - `Record`：錄製各種類型的數據，包括圖像和 .bag 文件
    - `RunSystem`：進行點雲數據處理
    - `View`：查看錄製和處理的點雲數據

## 貢獻指南

歡迎各界人士對本項目進行貢獻。請遵循以下步驟進行貢獻：

1. Fork 本存儲庫
2. 創建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. Push 到分支 (`git push origin feature/AmazingFeature`)
5. 打開一個 Pull Request

## 版權和許可

本項目採用 MIT 許可證。詳情請參閱 LICENSE 文件。

## 詳細文檔

有關詳細的項目目錄結構和介紹，請參閱 [docs/directory_structure.md](docs/directory_structure.md)。