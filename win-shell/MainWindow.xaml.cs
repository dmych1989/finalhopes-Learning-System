using System;
using System.Windows;
using System.Windows.Input;
using Microsoft.Web.WebView2.Core;

namespace FinalHopesShell;

/// <summary>
/// FinalHopes 学习系统的 Windows 桌面壳：用 WebView2 承载远程站点。
/// </summary>
public partial class MainWindow : Window
{
    /// <summary>壳加载的目标站点。</summary>
    private const string HomeUrl = "https://finalhopes.dynv6.net/";

    private bool _webReady;

    public MainWindow()
    {
        InitializeComponent();
        Loaded += OnLoaded;
    }

    private async void OnLoaded(object sender, RoutedEventArgs e)
    {
        try
        {
            LoadingPanel.Visibility = Visibility.Visible;

            // 将 WebView2 用户数据目录放到 %LOCALAPPDATA%，避免污染 exe 所在（可能只读）目录
            var userDataFolder = System.IO.Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "FinalHopes");
            var environment = await CoreWebView2Environment.CreateAsync(null, userDataFolder);
            await Web.EnsureCoreWebView2Async(environment);

            var core = Web.CoreWebView2;
            core.Settings.AreDefaultContextMenusEnabled = true;
            core.Settings.AreDevToolsEnabled = true;
            core.Settings.IsStatusBarEnabled = false;
            core.Settings.IsZoomControlEnabled = true;

            core.NavigationStarting += Core_NavigationStarting;
            core.NavigationCompleted += Core_NavigationCompleted;
            core.SourceChanged += Core_SourceChanged;
            core.DocumentTitleChanged += Core_DocumentTitleChanged;
            core.NewWindowRequested += Core_NewWindowRequested;
            core.ProcessFailed += Core_ProcessFailed;

            _webReady = true;
            core.Navigate(HomeUrl);
        }
        catch (Exception ex)
        {
            ShowError("无法初始化 WebView2 运行时。\n" +
                      "请确认本机已安装 Microsoft Edge WebView2 Runtime。\n\n" + ex.Message);
        }
    }

    private void Core_NavigationStarting(object? sender, CoreWebView2NavigationStartingEventArgs e)
    {
        LoadingPanel.Visibility = Visibility.Visible;
        ErrorPanel.Visibility = Visibility.Collapsed;
        FootText.Text = "正在打开 " + e.Uri;
    }

    private void Core_NavigationCompleted(object? sender, CoreWebView2NavigationCompletedEventArgs e)
    {
        LoadingPanel.Visibility = Visibility.Collapsed;
        UpdateNavButtons();

        if (e.IsSuccess)
        {
            FootText.Text = "加载完成";
        }
        else
        {
            FootText.Text = "加载失败：" + e.WebErrorStatus;
            ShowError("页面加载失败（" + e.WebErrorStatus + "）。\n请检查网络连接后重试。");
        }
    }

    private void Core_SourceChanged(object? sender, CoreWebView2SourceChangedEventArgs e)
    {
        AddressBar.Text = Web.Source?.ToString() ?? HomeUrl;
        UpdateNavButtons();
    }

    private void Core_DocumentTitleChanged(object? sender, object e)
    {
        var title = Web.CoreWebView2?.DocumentTitle;
        Title = string.IsNullOrWhiteSpace(title) ? "FinalHopes 学习系统" : title + " - FinalHopes";
    }

    private void Core_NewWindowRequested(object? sender, CoreWebView2NewWindowRequestedEventArgs e)
    {
        // 壳内不弹新窗口，统一在当前 WebView 中打开
        e.Handled = true;
        Web.CoreWebView2?.Navigate(e.Uri);
    }

    private void Core_ProcessFailed(object? sender, CoreWebView2ProcessFailedEventArgs e)
    {
        ShowError("WebView 进程异常退出（" + e.ProcessFailedKind + "）。\n请点击“重新加载”。");
    }

    private void UpdateNavButtons()
    {
        if (!_webReady || Web.CoreWebView2 is null) return;
        BtnBack.IsEnabled = Web.CoreWebView2.CanGoBack;
        BtnForward.IsEnabled = Web.CoreWebView2.CanGoForward;
    }

    private void ShowError(string message)
    {
        ErrorText.Text = message;
        LoadingPanel.Visibility = Visibility.Collapsed;
        ErrorPanel.Visibility = Visibility.Visible;
    }

    private void BtnBack_Click(object sender, RoutedEventArgs e)
    {
        if (_webReady && Web.CoreWebView2.CanGoBack) Web.CoreWebView2.GoBack();
    }

    private void BtnForward_Click(object sender, RoutedEventArgs e)
    {
        if (_webReady && Web.CoreWebView2.CanGoForward) Web.CoreWebView2.GoForward();
    }

    private void BtnRefresh_Click(object sender, RoutedEventArgs e)
    {
        if (_webReady) Web.CoreWebView2.Reload();
    }

    private void BtnHome_Click(object sender, RoutedEventArgs e)
    {
        if (_webReady) Web.CoreWebView2.Navigate(HomeUrl);
    }

    private void Retry_Click(object sender, RoutedEventArgs e)
    {
        ErrorPanel.Visibility = Visibility.Collapsed;
        if (_webReady) Web.CoreWebView2.Navigate(HomeUrl);
    }

    private void AddressBar_KeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key != Key.Enter || !_webReady) return;

        var input = AddressBar.Text.Trim();
        if (input.Length == 0) return;

        var url = input.Contains("://") ? input : "https://" + input;
        Web.CoreWebView2.Navigate(url);
    }
}
