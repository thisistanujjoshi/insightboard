using Admin.Web.Data;
using Admin.Web.Models;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Xunit;

namespace Admin.Tests;

public class TenantAdminTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly WebApplicationFactory<Program> _factory;

    public TenantAdminTests(WebApplicationFactory<Program> factory)
    {
        var dbName = $"admin-tests-{Guid.NewGuid()}";
        _factory = factory.WithWebHostBuilder(builder =>
        {
            builder.UseEnvironment("Testing");
            builder.ConfigureServices(services =>
            {
                // Replace the app's SQLite registration with the in-memory provider.
                foreach (var d in services
                    .Where(s => s.ServiceType == typeof(AdminDbContext)
                             || (s.ServiceType.FullName?.Contains("DbContextOptions") ?? false))
                    .ToList())
                {
                    services.Remove(d);
                }

                services.AddDbContext<AdminDbContext>(o => o.UseInMemoryDatabase(dbName));
            });
        });
    }

    private HttpClient Client() => _factory.CreateClient(
        new WebApplicationFactoryClientOptions { AllowAutoRedirect = false });

    private static string ExtractAntiForgeryToken(string html) =>
        System.Text.RegularExpressions.Regex
            .Match(html, "__RequestVerificationToken\" type=\"hidden\" value=\"([^\"]+)\"").Groups[1].Value;

    /// <summary>A client already carrying a valid auth cookie for the seeded
    /// demo admin (Auth:Users in appsettings.json) — TenantsController now
    /// requires the Admin role, so most tests need this instead of a bare
    /// Client().</summary>
    private async Task<HttpClient> LoggedInClientAsync(string username = "dana", string password = "dana123")
    {
        var client = Client();
        var loginPage = await client.GetStringAsync("/Account/Login");
        var token = ExtractAntiForgeryToken(loginPage);

        var response = await client.PostAsync("/Account/Login", new FormUrlEncodedContent(new Dictionary<string, string>
        {
            ["Username"] = username,
            ["Password"] = password,
            ["__RequestVerificationToken"] = token,
        }));
        Assert.Equal(System.Net.HttpStatusCode.Redirect, response.StatusCode);
        return client;
    }

    private async Task<Guid> AddTenantAsync(string name, TenantStatus status = TenantStatus.Active)
    {
        using var scope = _factory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AdminDbContext>();
        var tenant = new Tenant { Name = name, ContactEmail = "t@example.com", Status = status };
        db.Tenants.Add(tenant);
        await db.SaveChangesAsync();
        return tenant.Id;
    }

    private async Task<TenantStatus> StatusOfAsync(Guid id)
    {
        using var scope = _factory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AdminDbContext>();
        return (await db.Tenants.AsNoTracking().SingleAsync(t => t.Id == id)).Status;
    }

    [Fact]
    public async Task Index_ListsTenants()
    {
        await AddTenantAsync("Acme Widgets");
        var client = await LoggedInClientAsync();
        var html = await client.GetStringAsync("/Tenants");
        Assert.Contains("Acme Widgets", html);
    }

    [Fact]
    public async Task Create_Get_RendersForm()
    {
        var client = await LoggedInClientAsync();
        var html = await client.GetStringAsync("/Tenants/Create");
        Assert.Contains("Contact email", html);
    }

    [Fact]
    public async Task Suspend_ChangesStatus()
    {
        var id = await AddTenantAsync("SuspendMe");
        var client = await LoggedInClientAsync();

        // Fetch the index to obtain the antiforgery cookie + token.
        var index = await client.GetAsync("/Tenants");
        var html = await index.Content.ReadAsStringAsync();
        var token = ExtractAntiForgeryToken(html);

        var response = await client.PostAsync($"/Tenants/Suspend/{id}",
            new FormUrlEncodedContent(new Dictionary<string, string> { ["__RequestVerificationToken"] = token }));

        Assert.Equal(System.Net.HttpStatusCode.Redirect, response.StatusCode);
        Assert.Equal(TenantStatus.Suspended, await StatusOfAsync(id));
    }

    [Fact]
    public async Task Reactivate_RestoresStatus()
    {
        var id = await AddTenantAsync("WakeMe", TenantStatus.Suspended);
        var client = await LoggedInClientAsync();
        var html = await client.GetStringAsync("/Tenants");
        var token = ExtractAntiForgeryToken(html);

        var response = await client.PostAsync($"/Tenants/Reactivate/{id}",
            new FormUrlEncodedContent(new Dictionary<string, string> { ["__RequestVerificationToken"] = token }));

        Assert.Equal(System.Net.HttpStatusCode.Redirect, response.StatusCode);
        Assert.Equal(TenantStatus.Active, await StatusOfAsync(id));
    }

    [Fact]
    public async Task Suspend_UnknownTenant_Returns404()
    {
        var client = await LoggedInClientAsync();
        // The Create form always carries an antiforgery token, even with an empty DB.
        var html = await client.GetStringAsync("/Tenants/Create");
        var token = ExtractAntiForgeryToken(html);

        var response = await client.PostAsync($"/Tenants/Suspend/{Guid.NewGuid()}",
            new FormUrlEncodedContent(new Dictionary<string, string> { ["__RequestVerificationToken"] = token }));

        Assert.Equal(System.Net.HttpStatusCode.NotFound, response.StatusCode);
    }

    [Fact]
    public async Task Anonymous_GetTenants_RedirectsToLogin()
    {
        var response = await Client().GetAsync("/Tenants");
        Assert.Equal(System.Net.HttpStatusCode.Redirect, response.StatusCode);
        Assert.Contains("/Account/Login", response.Headers.Location?.ToString());
    }

    [Fact]
    public async Task Login_WithValidCredentials_GrantsAccessToTenants()
    {
        var client = await LoggedInClientAsync();
        var response = await client.GetAsync("/Tenants");
        Assert.Equal(System.Net.HttpStatusCode.OK, response.StatusCode);
    }

    [Fact]
    public async Task Login_WithInvalidCredentials_ShowsError()
    {
        var client = Client();
        var loginPage = await client.GetStringAsync("/Account/Login");
        var token = ExtractAntiForgeryToken(loginPage);

        var response = await client.PostAsync("/Account/Login", new FormUrlEncodedContent(new Dictionary<string, string>
        {
            ["Username"] = "dana",
            ["Password"] = "wrong-password",
            ["__RequestVerificationToken"] = token,
        }));

        Assert.Equal(System.Net.HttpStatusCode.OK, response.StatusCode);
        Assert.Contains("Invalid username or password", await response.Content.ReadAsStringAsync());
    }
}
