using System.Security.Claims;
using Admin.Web.Models;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Mvc;

namespace Admin.Web.Controllers;

public class AccountController(IConfiguration configuration) : Controller
{
    [HttpGet]
    public IActionResult Login(string? returnUrl = null) => View(new LoginViewModel { ReturnUrl = returnUrl });

    [HttpPost, ValidateAntiForgeryToken]
    public async Task<IActionResult> Login(LoginViewModel model)
    {
        if (!ModelState.IsValid) return View(model);

        var user = configuration.GetSection("Auth:Users").Get<List<DemoUser>>()?
            .FirstOrDefault(u =>
                string.Equals(u.Username, model.Username, StringComparison.OrdinalIgnoreCase)
                && u.Password == model.Password);

        if (user is null)
        {
            ModelState.AddModelError(string.Empty, "Invalid username or password.");
            return View(model);
        }

        var claims = new List<Claim> { new(ClaimTypes.Name, user.Username), new(ClaimTypes.Role, user.Role) };
        var identity = new ClaimsIdentity(claims, CookieAuthenticationDefaults.AuthenticationScheme);
        await HttpContext.SignInAsync(CookieAuthenticationDefaults.AuthenticationScheme, new ClaimsPrincipal(identity));

        return LocalRedirect(Url.IsLocalUrl(model.ReturnUrl) ? model.ReturnUrl! : "/");
    }

    [HttpPost, ValidateAntiForgeryToken]
    public async Task<IActionResult> Logout()
    {
        await HttpContext.SignOutAsync(CookieAuthenticationDefaults.AuthenticationScheme);
        return RedirectToAction(nameof(Login));
    }
}
