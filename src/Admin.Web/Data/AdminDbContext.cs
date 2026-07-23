using Admin.Web.Models;
using Microsoft.EntityFrameworkCore;

namespace Admin.Web.Data;

public class AdminDbContext(DbContextOptions<AdminDbContext> options) : DbContext(options)
{
    public DbSet<Tenant> Tenants => Set<Tenant>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Tenant>(t =>
        {
            t.HasIndex(x => x.Name).IsUnique();
            t.Property(x => x.Plan).HasConversion<string>();
            t.Property(x => x.Status).HasConversion<string>();
        });
    }

    public static async Task SeedAsync(AdminDbContext db)
    {
        await db.Database.EnsureCreatedAsync();
        if (await db.Tenants.AnyAsync()) return;

        db.Tenants.AddRange(
            new Tenant { Name = "NexusCommerce Demo Shop", ContactEmail = "owner@nexus.example", Plan = PlanKind.Pro },
            new Tenant { Name = "Priya Electronics", ContactEmail = "priya@example.com", Plan = PlanKind.Free },
            new Tenant { Name = "Marco Retail Group", ContactEmail = "marco@example.com", Plan = PlanKind.Pro, Status = TenantStatus.Suspended });
        await db.SaveChangesAsync();
    }
}
