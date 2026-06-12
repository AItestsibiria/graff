module.exports = {
  apps: [{
    name: "graff-server",
    script: "/var/www/biznesmetr/tools/graff/.venv/bin/python",
    args: "-m graff.server",
    cwd: "/var/www/biznesmetr/tools/graff",
    env: {
      GRAFF_PORT: "8765",
      GRAFF_DATA: "/var/graff-saas",
      GRAFF_API_KEYS: "",   // заполнить: GRAFF_API_KEYS=key1,key2
      PYTHONWARNINGS: "ignore",
    },
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: "512M",
    error_file: "/var/log/graff/error.log",
    out_file: "/var/log/graff/out.log",
  }],
};
