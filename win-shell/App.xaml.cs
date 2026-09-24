using System.Windows;

namespace FinalHopesShell;

/// <summary>
/// Application entry point.
/// </summary>
public partial class App : Application
{
    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);

        // 未处理异常兜底：避免壳在异常时静默退出
        DispatcherUnhandledException += (_, args) =>
        {
            MessageBox.Show(
                "程序发生未处理的错误：\n\n" + args.Exception.Message,
                "FinalHopes 学习系统",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
            args.Handled = true;
        };
    }
}
