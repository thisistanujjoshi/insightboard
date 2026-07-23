using Admin.Web.Data;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllersWithViews();

// SQLite for local dev; tests swap this for the in-memory provider.
if (!string.Equals(builder.Configuration["Database:Provider"], "InMemory", StringComparison.OrdinalIgnoreCase))
    builder.Services.AddDbContext<AdminDbContext>(o =>
        o.UseSqlite(builder.Configuration.GetConnectionString("AdminDb") ?? "Data Source=admin.dev.db"));

var app = builder.Build();

if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Home/Error");
}
app.UseRouting();

app.UseAuthorization();

app.MapStaticAssets();

app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Tenants}/{action=Index}/{id?}")
    .WithStaticAssets();

if (app.Environment.IsDevelopment())
{
    using var scope = app.Services.CreateScope();
    await AdminDbContext.SeedAsync(scope.ServiceProvider.GetRequiredService<AdminDbContext>());
}

app.Run();

public partial class Program;
