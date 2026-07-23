using System.ComponentModel.DataAnnotations;

namespace Admin.Web.Models;

public enum PlanKind { Free = 0, Pro = 1 }

public enum TenantStatus { Active = 0, Suspended = 1 }

public class Tenant
{
    public Guid Id { get; set; } = Guid.NewGuid();

    [Required, StringLength(100)]
    public string Name { get; set; } = "";

    [Required, EmailAddress, StringLength(320)]
    [Display(Name = "Contact email")]
    public string ContactEmail { get; set; } = "";

    public PlanKind Plan { get; set; } = PlanKind.Free;

    public TenantStatus Status { get; set; } = TenantStatus.Active;

    public DateTime CreatedAtUtc { get; set; } = DateTime.UtcNow;
}
