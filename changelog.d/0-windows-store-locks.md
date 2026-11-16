### Fixed

- Dateibasierte Konfigurations- und Secret-Stores funktionieren auch unter Windows: gemeinsame Prozesssperren verwenden dort `msvcrt` und unter POSIX weiterhin `flock`, statt beim Import an `fcntl` zu scheitern.
