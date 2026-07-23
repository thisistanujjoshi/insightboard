using Admin.Web.Data;
using Admin.Web.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace Admin.Web.Controllers;

[Authorize(Roles = "Admin")]
public class TenantsController(AdminDbContext db) : Controller
{
    public async Task<IActionResult> Index()
    {
        var tenants = await db.Tenants.OrderBy(t => t.Name).ToListAsync();
        return View(tenants);
    }

    public IActionResult Create() => View(new Tenant());

    [HttpPost, ValidateAntiForgeryToken]
    public async Task<IActionResult> Create(Tenant tenant)
    {
        if (await db.Tenants.AnyAsync(t => t.Name == tenant.Name))
            ModelState.AddModelError(nameof(Tenant.Name), "A tenant with this name already exists.");
        if (!ModelState.IsValid)
            return View(tenant);

        tenant.Id = Guid.NewGuid();
        tenant.CreatedAtUtc = DateTime.UtcNow;
        db.Tenants.Add(tenant);
        await db.SaveChangesAsync();
        TempData["Flash"] = $"Tenant '{tenant.Name}' created.";
        return RedirectToAction(nameof(Index));
    }

    public async Task<IActionResult> Edit(Guid id)
    {
        var tenant = await db.Tenants.FindAsync(id);
        return tenant is null ? NotFound() : View(tenant);
    }

    [HttpPost, ValidateAntiForgeryToken]
    public async Task<IActionResult> Edit(Guid id, Tenant form)
    {
        var tenant = await db.Tenants.FindAsync(id);
        if (tenant is null) return NotFound();
        if (!ModelState.IsValid) return View(form);

        tenant.Name = form.Name;
        tenant.ContactEmail = form.ContactEmail;
        tenant.Plan = form.Plan;
        await db.SaveChangesAsync();
        TempData["Flash"] = $"Tenant '{tenant.Name}' updated.";
        return RedirectToAction(nameof(Index));
    }

    [HttpPost, ValidateAntiForgeryToken]
    public async Task<IActionResult> Suspend(Guid id)
    {
        var tenant = await db.Tenants.FindAsync(id);
        if (tenant is null) return NotFound();
        tenant.Status = TenantStatus.Suspended;
        await db.SaveChangesAsync();
        TempData["Flash"] = $"Tenant '{tenant.Name}' suspended.";
        return RedirectToAction(nameof(Index));
    }

    [HttpPost, ValidateAntiForgeryToken]
    public async Task<IActionResult> Reactivate(Guid id)
    {
        var tenant = await db.Tenants.FindAsync(id);
        if (tenant is null) return NotFound();
        tenant.Status = TenantStatus.Active;
        await db.SaveChangesAsync();
        TempData["Flash"] = $"Tenant '{tenant.Name}' reactivated.";
        return RedirectToAction(nameof(Index));
    }
}
