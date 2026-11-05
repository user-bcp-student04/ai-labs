## ADDED Requirements

### Requirement: Credenciales válidas inician sesión
`POST /auth/login` SHALL responder 200 con `token`, `expiresIn`, `user` (`username`, `displayName`, `role`) cuando `username` y `password` coinciden con un usuario registrado.

#### Scenario: Login con usuario del taller
- **WHEN** se envía `POST /auth/login` con `username` `student` y `password` `Workshop123!`
- **THEN** la respuesta es 200
- **AND** `user.username` es `student`
- **AND** `token` no es nulo

### Requirement: Credenciales inválidas se rechazan
`POST /auth/login` SHALL responder 401 sin `token` cuando el par `username`/`password` no coincide con ningún usuario.

#### Scenario: Contraseña incorrecta
- **WHEN** se envía `username` `student` y `password` `incorrecta`
- **THEN** la respuesta es 401
- **AND** el cuerpo no contiene `token`

#### Scenario: Usuario inexistente
- **WHEN** se envía `username` `noexiste` y `password` `Workshop123!`
- **THEN** la respuesta es 401
- **AND** el cuerpo no contiene `token`

### Requirement: Los valores de credenciales no alteran la consulta
El sistema SHALL tratar `username` y `password` como datos literales al consultar credenciales; ningún valor recibido SHALL modificar la estructura de la consulta SQL. La consulta de credenciales SHALL usar `PreparedStatement` con parámetros y SHALL NOT concatenar esos valores en el SQL.

#### Scenario: Inyección en el campo usuario
- **WHEN** se envía `username` `' OR '1'='1` y una `password` cualquiera
- **THEN** la respuesta es 401
- **AND** el cuerpo no contiene `token`

#### Scenario: Inyección en el campo contraseña
- **WHEN** se envía `username` `student` y `password` `' OR '1'='1`
- **THEN** la respuesta es 401
- **AND** el cuerpo no contiene `token`

#### Scenario: Inyección con comentario SQL
- **WHEN** se envía `username` `student'--` y una `password` cualquiera
- **THEN** la respuesta es 401
- **AND** el cuerpo no contiene `token`

### Requirement: Validación de entrada preservada
`POST /auth/login` SHALL responder 400 con `message` cuando el request es nulo, o `username` o `password` están ausentes o vacíos, sin consultar credenciales.

#### Scenario: Usuario vacío
- **WHEN** se envía `username` vacío y `password` `Workshop123!`
- **THEN** la respuesta es 400
- **AND** `message` es `Username is required`

#### Scenario: Contraseña vacía
- **WHEN** se envía `username` `student` y `password` vacío
- **THEN** la respuesta es 400
- **AND** `message` es `Password is required`

### Requirement: Intento de inyección verificado por pruebas
`AuthResourceTest` SHALL incluir al menos una prueba del intento de inyección SQL y `mvn test` SHALL pasar al ejecutarse desde `auth/`.

#### Scenario: Suite de auth
- **WHEN** se ejecuta `mvn test` desde `auth/`
- **THEN** pasan las pruebas, incluida la del intento de inyección