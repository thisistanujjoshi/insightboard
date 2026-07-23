namespace Admin.Web.Models;

/// <summary>A config-seeded demo credential (Auth:Users in appsettings) — no
/// user store; this back office has a handful of internal admins, not a
/// self-serve signup flow.</summary>
public class DemoUser
{
    public string Username { get; set; } = "";
    public string Password { get; set; } = "";
    public string Role { get; set; } = "Admin";
}
