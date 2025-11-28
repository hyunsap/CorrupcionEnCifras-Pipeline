# Pipeline de Datos de Corrupción

Pipeline automatizado de scraping, ETL y carga de datos de casos de corrupción.

## 📋 Prerequisitos

- Docker y Docker Compose instalados
- Al menos 2GB de espacio libre en disco
- Conexión a Internet para el scraping

## 🚀 Inicio Paso a Paso

### 1. Clonar el Repositorio
```bash
git clone https://github.com/hyunsap/CorrupcionEnCifras-Pipeline
cd corrupcion-pipeline
```

### 2. Crear Carpeta de Logs
```bash
mkdir -p logs
```

### 3. Iniciar los Servicios
```bash
docker-compose up -d 

# Esperar a que la base de datos esté lista (unos 10 segundos)
docker-compose logs -f postgres
# Presionar Ctrl+C cuando veas "database system is ready to accept connections"
```

### 4. Ejecutar Pipeline (Primera Vez)
```bash
# Ejecutar el pipeline completo
./run_pipeline.sh

# En Windows, usar Git Bash para ejecutar el script
```

O ejecutar cada paso individualmente:
```bash
# Paso 1: Ejecutar scrapers
docker-compose run --rm scraper

# Paso 2: Ejecutar ETL
docker-compose run --rm etl

# Paso 3: Cargar datos
docker-compose run --rm loader
```

## 📅 Ejecución Automática Semanal

El pipeline se ejecuta automáticamente cada **Domingo a las 2:00 AM** mediante el servicio scheduler.

El cronograma:
- **2:00 AM** - Los scrapers se ejecutan (generan CSVs)
- **4:00 AM** - ETL procesa los CSVs (2 horas después de los scrapers)
- **4:15 AM** - Loader inserta datos en la base de datos

Para modificar el cronograma, editar las etiquetas `ofelia.job-run.*.schedule` en `docker-compose.yml`.


## 🤝 Ejecución Completa

Para ejecutar este pipeline:

1. Instalar Docker y Docker Compose
2. Clonar este repositorio
3. Crear carpeta de logs: `mkdir -p logs`
4. Ejecutar `docker-compose up -d`
5. Ejecutar `./run_pipeline.sh` (usar Git Bash en Windows)
6. El pipeline se ejecutará automáticamente cada Domingo

¡Eso es todo! Sin necesidad de configurar entorno de Python ni problemas de dependencias.

## 📊 Monitoreo

### Verificar Estado del Planificador
```bash
docker-compose logs -f scheduler
```

### Verificar Logs de Última Ejecución
```bash
# Logs del scraper
ls -lht logs/scraper_*.log | head -1

# Logs del ETL
docker-compose logs etl

# Logs del loader
docker-compose logs loader
```

### Ver CSVs Generados
```bash
ls -lh data/
```

### Consultar Base de Datos
```bash
# Conectarse a la base de datos
docker-compose exec postgres psql -U admin -d corrupcion_db

# Verificar cantidad de filas
SELECT tablename, n_live_tup 
FROM pg_stat_user_tables 
ORDER BY n_live_tup DESC;
```

## 🛠️ Comandos de Gestión

### Detener Todos los Servicios
```bash
docker-compose down
```

### Detener y Eliminar Todos los Datos
```bash
docker-compose down -v
# ADVERTENCIA: ¡Esto elimina la base de datos!
```

### Reiniciar un Servicio Específico
```bash
docker-compose restart scheduler
```

### Reconstruir Después de Cambios en el Código
```bash
docker-compose build scraper etl loader
```

## 🔧 Configuración

### Conexión a Base de Datos

Las credenciales están configuradas en `docker-compose.yml`:
- Puerto: `5433`
- Base de datos: `corrupcion_db`
- Usuario: `admin`
- Contraseña: `td8corrupcion`

## 🔍 Solución de Problemas

### Si la base de datos no inicia
```bash
# Verificar logs
docker-compose logs postgres

# Resetear base de datos
docker-compose down -v
docker-compose up -d postgres
```

### Si el scraper falla
```bash
# Verificar logs
docker-compose logs scraper
cat logs/scraper_*.log | tail -50
```

### Si el ETL falla
```bash
# Verificar si existen los CSVs
ls -lh data/

# Verificar logs del ETL
docker-compose logs etl
```

## 🔒 Notas de Seguridad

- **¡Cambiar las contraseñas por defecto** en producción!
- Restringir el puerto de la base de datos (5433) en producción