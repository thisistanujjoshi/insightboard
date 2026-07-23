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
        var html = await _factory.CreateClient().GetStringAsync("/Tenants");
        Assert.Contains("Acme Widgets", html);
    }

    [Fact]
    public async Task Create_Get_RendersForm()
    {
        var html = await _factory.CreateClient().GetStringAsync("/Tenants/Create");
        Assert.Contains("Contact email", html);
    }

    [Fact]
    public async Task Suspend_ChangesStatus()
    {
        var id = await AddTenantAsync("SuspendMe");
        var client = Client();

        // Fetch the index to obtain the antiforgery cookie + token.
        var index = await client.GetAsync("/Tenants");
        var html = await index.Content.ReadAsStringAsync();
        var token = System.Text.RegularExpressions.Regex
            .Match(html, "__RequestVerificationToken\" type=\"hidden\" value=\"([^\"]+)\"").Groups[1].Value;

        var response = await client.PostAsync($"/Tenants/Suspend/{id}",
            new FormUrlEncodedContent(new Dictionary<string, string> { ["__RequestVerificationToken"] = token }));

        Assert.Equal(System.Net.HttpStatusCode.Redirect, response.StatusCode);
        Assert.Equal(TenantStatus.Suspended, await StatusOfAsync(id));
    }

    [Fact]
    public async Task Reactivate_RestoresStatus()
    {
        var id = await AddTenantAsync("WakeMe", TenantStatus.Suspended);
        var client = Client();
        var html = await client.GetStringAsync("/Tenants");
        var token = System.Text.RegularExpressions.Regex
            .Match(html, "__RequestVerificationToken\" type=\"hidden\" value=\"([^\"]+)\"").Groups[1].Value;

        var response = await client.PostAsync($"/Tenants/Reactivate/{id}",
            new FormUrlEncodedContent(new Dictionary<string, string> { ["__RequestVerificationToken"] = token }));

        Assert.Equal(System.Net.HttpStatusCode.Redirect, response.StatusCode);
        Assert.Equal(TenantStatus.Active, await StatusOfAsync(id));
    }

    [Fact]
    public async Task Suspend_UnknownTenant_Returns404()
    {
        var client = Client();
        // The Create form always carries an antiforgery token, even with an empty DB.
        var html = await client.GetStringAsync("/Tenants/Create");
        var token = System.Text.RegularExpressions.Regex
            .Match(html, "__RequestVerificationToken\" type=\"hidden\" value=\"([^\"]+)\"").Groups[1].Value;

        var response = await client.PostAsync($"/Tenants/Suspend/{Guid.NewGuid()}",
            new FormUrlEncodedContent(new Dictionary<string, string> { ["__RequestVerificationToken"] = token }));

        Assert.Equal(System.Net.HttpStatusCode.NotFound, response.StatusCode);
    }
}
