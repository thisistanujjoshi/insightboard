# Multi-stage build for the Admin.Web back office.
# Build context is the repository root (see docker-compose / CI).
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

COPY src/Admin.Web/Admin.Web.csproj src/Admin.Web/
RUN dotnet restore src/Admin.Web/Admin.Web.csproj

COPY src/Admin.Web/ src/Admin.Web/
RUN dotnet publish src/Admin.Web/Admin.Web.csproj -c Release -o /app --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS runtime
# curl is used by the container healthcheck (the runtime image ships without it).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=build /app ./

# Run as the non-root user the aspnet image provides.
USER $APP_UID
ENV ASPNETCORE_HTTP_PORTS=8080
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --retries=10 \
    CMD curl -fsS http://localhost:8080/health || exit 1
ENTRYPOINT ["dotnet", "Admin.Web.dll"]
