---
title: Arquitecturas EDA Eventos de dominio vs eventos de integración
author: Benjamin
date: 2024-02-12 00:00:00 -0500
categories: Arquitectura Software,DDD,Events architecture,Backend
tags: arquitectura software,ddd,events architecture,backend
---


![intro](assets/img/intros/intro4.webp)


La comunicación asíncrona entre microservicios nos ayuda a crear procesos complejos donde las responsabilidades del sistema están repartidas entre distintas aplicaciones. Como es la filosofía de los microservicios, separar responsabilidades para mantener ciertas características independientes entre sí nos ayuda a lograr escalabilidad, manejo de cargas y tolerancia a errores, pero esto conlleva un gran desafío de comunicación. Comunicar un servicio de forma síncrona y esperar una respuesta no siempre es viable. Hay cargas de trabajo que no requieren una respuesta inmediata, e incluso muchas veces esto puede fallar y romper todo el flujo de un proceso importante. Nadie quiere esto en una compra de considerable valor.

Cuando la comunicación síncrona no es la opción, te presento las arquitecturas EDA, o arquitecturas basadas en eventos. Este enfoque nos da la posibilidad de comunicarnos con componentes tanto internos de una aplicación como con servicios o aplicaciones externas. En esta ocasión analizaremos los eventos de dominio y los eventos de integración.

## Comunicación basada en eventos

La integración de aplicaciones y servicios utilizando arquitecturas orientadas a eventos es esencial para crear sistemas robustos y flexibles. Dos conceptos fundamentales en este ámbito son los eventos de dominio y los eventos de integración. Ambos desempeñan roles cruciales, pero se aplican en contextos un tanto diferentes, pero a su vez son compatibles entre sí, lo que nos permite crear sistemas complejos y desacoplados.

### Eventos de Dominio:

Los eventos de dominio son fundamentales en el diseño basado en dominio o DDD, una técnica que se centra en modelar el sistema según el dominio de negocio al que pertenece. Estos eventos representan cambios significativos en el estado del dominio y suelen estar vinculados estrechamente a los conceptos del modelo de dominio. También representan hechos pasados del dominio, por ejemplo: `user-created`, `user-banned`, `stock-updated`, etc.

> Si bien los eventos de dominio los encuentras mucho en sistemas hechos con DDD, nadie te impide usarlos en arquitecturas más simples como las de N-capas.

#### Características Clave:

- **Contexto de Negocio**: Los eventos de dominio se originan en el núcleo del negocio y reflejan acciones o cambios relevantes para el dominio.
- **Desacoplamiento**: Permiten un desacoplamiento eficiente entre las distintas partes del sistema al enfocarse en la semántica del dominio en lugar de detalles de implementación.
- **Modelado Preciso**: Al reflejar eventos específicos del dominio, estos eventos contribuyen a un modelado más preciso y representativo del negocio.

### Eventos de Integración:

Los eventos de integración son mensajes diseñados para coordinar la interacción entre microservicios o aplicaciones. Estos eventos abordan la necesidad de sincronización y colaboración en un entorno distribuido. Estos eventos representan mensajes que se intercambian entre componentes o servicios para mantener la coherencia y la sincronización en el ecosistema de software.

#### Características Clave:

- **Comunicación Inter-Servicios**: Los eventos de integración facilitan la comunicación entre diferentes servicios o componentes, permitiendo la colaboración en un entorno distribuido.
- **Desacoplamiento de Sistemas**: Al utilizar eventos para la integración, se logra un desacoplamiento efectivo entre sistemas, lo que facilita la escalabilidad y la evolución independiente de cada componente.
- **Interoperabilidad**: Son esenciales para lograr interoperabilidad entre sistemas heterogéneos, ya que proporcionan un medio estandarizado de intercambio de información.

Es crucial comprender que los eventos de dominio y los eventos de integración sirven propósitos diferentes, pero no son mutuamente excluyentes. De hecho, su uso combinado puede potenciar la eficacia de un sistema.

## Casos de Uso Eventos de dominio:

En nuestra arquitectura de nuestro **Spotify-clone** veremos los eventos de dominio ocurridos en el microservicio `music-discovery-ms`. Esta aplicación contiene los siguientes módulos:

- **user-catalog**: catálogo musical del usuario con playlists personales, artistas y canciones favoritas.
- **playlist-catalog**: catálogo de playlists ofrecidas a los usuarios.
- **shared**: componentes compartidos entre los módulos.

### Caso de uso: El catálogo de playlists públicos debe actualizarse si el usuario actualiza sus playlists de tipo público.

Cuando el usuario crea una playlist en su catálogo, si esta es de tipo público, debe agregarse automáticamente al catálogo de playlists de **Spotify-clone** para poder ser indexado de forma eficiente.

Analizando el caso de uso, lo único que tendríamos que hacer es invocar al repositorio encargado de la playlist de **Spotify-clone** cuando el usuario actualice su playlist. Pero para ejemplos reales, suponiendo que la complejidad del código es alta, acoplar el módulo `user-catalog` con `playlist-catalog` en el caso de uso de actualizar catálogo de usuario no tiene nada que ver con el caso de uso de actualizar el catálogo de playlist. Esto incluso no nos permite que nuestro código sea escalable. Para solucionar esto, comunicaremos estos 2 módulos mediante eventos de dominio.

Primero creamos dentro de la librería `libs/utils` del proyecto monorepo una librería de utilitarios de DDD llamada `seedwork` con clase base para los eventos de dominio.

> `seedwork` El nombre hace referencia a un tipo de mini framework de utilidades propias, pero aplicado a nivel local de tu proyecto. Puedes encontrarlo con otros nombres como shared-kernel, commons, core, etc.

```typescript
//libs/utils/src/seedwork/domain/events/eventbus.ts
export abstract class DomainEventBus {
    abstract publish<T extends DomainEvent<any>>(event: T): void
}
//libs/utils/src/seedwork/domain/events/domain.event.ts
export abstract class DomainEvent<T = any> {

    public readonly id: string;
    public readonly occurredOn: Date;
    
    constructor(
        public readonly name: string,
        public readonly payload: T
    ) {
        this.id = uuid.generate();
        this.occurredOn = new Date();
    }

}
```

Nos ayudamos de la librería [eventemitter](https://docs.nestjs.com/techniques/events) de NestJS para crear un eventbus en memoria para poder emitir los eventos.

```typescript
// libs/utils/src/seedwork/infrastructure/domain-eventbus/services/event-emitter.eventbus.ts
@Injectable()
export class EventEmitterEventbus implements DomainEventBus {

    constructor(private eventEmitter: EventEmitter2) {}
   
    async publish<T extends DomainEvent<any>>(event: T) {
        this.eventEmitter.emit(event.name, event);
    }

}
```

Generamos los eventos de dominio dentro del módulo `shared` de `music-discovery`.

```typescript
// apps/music-discovery-ms/src/shared/domain-events/user-music-catalog/playlist-updated.event.ts
export class PlaylistUpdatedEvent extends DomainEvent<Playlist> { 
    
    constructor(playlist: Playlist) {
        super(PlaylistUpdatedEvent.NAME, playlist);
    }

    static readonly NAME = 'com.clonespotify.discovery.user-music-catalog.domain.playlist-updated';
    
}
```

> Utilizamos el patrón de spotifyclone.*FEATURE*.domain.*EVENT* para poder realizar patrones de filtrado sobre eventos en casos más complejos.

Ahora nuestro caso de uso sería el siguiente.

```typescript
// apps/music-discovery-ms/src/user-catalog/application/dto/update-playlists.dto.ts
export class UpdatePlaylistsDto {
    
    @IsUUID()
    @IsNotEmpty()
    userCatalogId: string;

    @ValidateNested({ each: true })
    playlist: Playlist;
    
}
// apps/music-discovery-ms/src/user-catalog/domain/model/playlist.model.ts
export class Playlist extends Model {
    
    @IsNotEmpty()
    name: string;
    
    @IsBoolean()
    isPublic: boolean;
    
    @IsArray()
    @ValidateNested({ each: true })
    @Type(() => Song)
    songs: Song[];

}
// apps/music-discovery-ms/src/user-catalog/application/user-catalog.use-cases.ts
@Injectable()
export class UserCatalogUseCases {

    constructor(
        private readonly catalog: UserCatalogService,
        private readonly domainEventbus: DomainEventBus
    ) { }

    async updatePlaylists(dto: UpdatePlaylistsDto) {

        const playlistNotToUpdate = (playlists) => playlists.filter(p => p.id !== dto.playlist.id);

        return await this.catalog.findById(dto.userCatalogId)
            .then(catalog => {
                catalog.playlists = [
                    ...playlistNotToUpdate(catalog.playlists),
                    dto.playlist
                ]
                return catalog
            })
            .then(async catalog => {
                await this.catalog.save(catalog)
                return catalog
            })
            .then(catalog => {
                this.domainEventbus.publish(new PlaylistUpdatedEvent(dto.playlist));
                return catalog
            });

    }

}
```

Nuestro caso de uso es simple, solo recibimos un DTO con la información de la playlist a actualizar y enviamos el evento de dominio con `domainEventBus.publish()`.

Gracias a NestJS podremos escuchar este evento mediante anotaciones en cualquier servicio `@Injectable`.

```typescript
// apps/music-discovery-ms/src/playlist-catalog/infrastructure/domain-events/domain-event.listener.ts
@Injectable()
export class DomainEventListener {

    constructor(private readonly playlist: PlaylistUseCases) {}

    @OnEvent('com.clonespotify.discovery.user-music-catalog.domain.playlist-updated')
    async onPlaylistCreated(event: PlaylistUpdatedEvent) {
        const playlist = event.payload
        if (playlist.isPublic) {
            await this.playlist.create(playlist)
        }
    }

}
```

Finalmente, recibimos la playlist mediante un evento y si esta es pública, se guardará en la base de datos en el módulo de `playlist-catalog`. De esta manera, hemos desacoplado 2 casos de uso totalmente distintos donde el modelo de playlist tiene un significado distinto dependiendo del contexto de dominio en que esté.

## Casos de Uso Eventos de integración:

Ya tenemos claro que los eventos de integración nos ayudan a comunicar distintas aplicaciones. Para ejemplificar este concepto, tomaremos el caso de uso de creación de usuario dentro del microservicio `accounts-ms`, el cual es dependiente de un caso de uso más grande llamado "Bienvenida de usuario".

### Caso de uso: Bienvenida de usuario

Este caso de uso involucra 3 aplicaciones:
- `account-ms`: encargado de la gestión de cuentas y usuarios.
- `mailing-ms`: encargado de enviar notificaciones de correo electrónico.
- `music-discovery-ms`: encargado de gestionar la música que le interesa o puede interesarle al usuario del clonespotify.

Nuestro caso de uso es simple. Cuando se cree un usuario dentro de `accounts-ms`, necesitamos enviar un correo electrónico de bienvenida al usuario y a su vez necesitamos iniciar el catálogo inicial del usuario.

Este simple caso de uso involucra diferentes servicios, y como vemos a simple vista, cada uno de estos tiene responsabilidades totalmente distintas entre sí, pero gracias a los eventos de integración podemos lograr un proceso distribuido entre nuestros servicios con un bajo acoplamiento.

Lo primero será definir la arquitectura de eventos. Para lograrlo, nos ayudaremos del modelo `pub/sub`, el cual nos permitirá que múltiples clientes puedan suscribirse a algún evento y realizar sus operaciones.

Creemos un servicio de Redis en nuestro docker-compose.

```yml
# infrastructure/local/docker-compose.yaml
version: '3'
services:
  # ... other services
  redis:
    container_name: redis
    image: redis:6.2-alpine
    restart: always
    ports:
      - ${REDIS_PORT}:6379
    command: redis-server --save 20 1 --loglevel warning --requirepass ${REDIS_PASS}
    networks:
      - microservices-architecture
```

Instalamos la siguiente dependencia.

```bash
npm i --save ioredis 
```

NestJS nos ofrece este modelo de `pub/sub` basado en un servidor Redis, el cual nos ayudará a aplicar y escuchar eventos a modo de fire and forget, lo que implica la desventaja de que si nadie escucha los mensajes emitidos, estos se perderán. Pero a modo de aprendizaje, esto nos bastará.

La implementación del `pub/sub` es simple, así que definimos la siguiente librería compartida en nuestro monorepo.

```bash
 integration-events
├──  src
│   ├──  config
│   │   └──  constants.ts
│   ├──  events
│   │   ├──  accounts-ms
│   │   │   └──  user-created.event.ts
│   │   ├──  integration.event.ts
│   │   ├──  integration.eventbus.ts
│   │   └──  music-discovery-ms
│   │       └──  user-favorites-updated.event.ts
│   ├──  index.ts
│   ├──  integration-events.module.ts
│   ├──  services
│   │   └──  redis.eventbus.ts
│   └──  transporters
│       ├──  get-microservice-options.ts
│       └──  redis
│           └──  get-redis-options.ts
└──  tsconfig.lib.json
```

Definimos nuestro Eventbus.

```typescript
// libs/integration-events/src/events/integration.eventbus.ts
export abstract class IntegrationEventBus {

    abstract publish<T>(event: IntegrationEvent<T>): IntegrationEvent<T>;

}
// libs/integration-events/src/services/redis.eventbus.ts
@Injectable()
export class RedisEventBus extends IntegrationEventBus {

    constructor(@Inject(REDIS_PRODUCER_CLIENT) private client: ClientProxy) {
        super()
    }

    publish<T>(event: IntegrationEvent<T>): IntegrationEvent<T> {
        this.client.emit(event.name, event)
        return event
    }

}
// libs/integration-events/src/integration-events.module.ts
const IntegrationEventbusProvider = {
  provide: IntegrationEventBus,
  useExisting: RedisEventBus
}

@Module({
  providers: [
    RedisEventBus,
    IntegrationEventbusProvider
  ],
  exports: [
    IntegrationEventbusProvider
  ],
  imports: [
    ClientsModule.registerAsync([
      {
        name: REDIS_PRODUCER_CLIENT,
        imports: [
          ConfigModule.forRoot()
        ],
        useFactory: (config: ConfigService) => {
          const host = config.get('REDIS_HOST')
          const port = config.get('REDIS_PORT')
          const password = config.get('REDIS_PASS') 
          return {
            transport: Transport.REDIS,
            options: {
              host,
              port,
              password
            }
          }
        },
        inject: [
          ConfigService
        ]
      },
    ]),
  ]

})
export class IntegrationEventsModule { }
```

Definimos los eventos.

```typescript
// libs/integration-events/src/events/integration.event.ts
export abstract class IntegrationEvent<T> {

    public readonly id: string;
    public readonly occurredOn: Date;
    
    constructor(
        public readonly service: string,
        public readonly name: string,
        public readonly payload: T
    ) {
        this.id = uuid.generate();
        this.occurredOn = new Date();
    }

}
// libs/integration-events/src/events/accounts-ms/user-created.event.ts
export interface Payload {
    id: string;
    username: string;
    email: string;
}

export class UserCreatedEvent extends IntegrationEvent<Payload> {
    constructor(payload: Payload) {
        super('accounts-ms', 'com.clonespotify.accounts.users.integration.user-updated', payload);
    }
}
```

### Enviar eventos de integración

Ahora, dentro del módulo `users` de `accounts-ms`, importamos nuestra librería para instanciar el eventbus.

```typescript
// apps/accounts-ms/src/users/users.module.ts
@Module({
    // ...more code
    imports:[
        IntegrationEventsModule
    ]
})
export class UsersModule {}
```

Y hacemos uso de `IntegrationEventBus` dentro de nuestro servicio UserService.

```typescript
// apps/accounts-ms/src/users/service/user.service.ts
@Injectable()
export class UserService {
  
  constructor(
    @InjectRepository(User) private repository: Repository<User>,
    private readonly integrationEventBus: IntegrationEventBus
  ) {}

  async create(user: UserModel): Promise<User> {
    const userCreated = await this.repository.save(user);
    this.integrationEventBus.publish(new UserCreatedEvent({
      id: userCreated.id,
      username: userCreated.username,
      email: userCreated.email
    }));
    return userCreated;
  }

}
```

Con esto, los eventos serán enviados al servidor Redis y quienes estén a la escucha obtendrán los mensajes.

### Escuchar eventos de integración

Ahora, para escuchar los eventos, instanciamos nuestro microservicio NestJS en las aplicaciones que necesiten los eventos de integración.

```typescript
// libs/integration-events/src/transporters/get-microservice-options.ts
export function getMicroserviceOptions() {
    return {
        transport: Transport.REDIS,
        options: {
            host: process.env.REDIS_HOST || 'localhost',
            port: process.env.REDIS_PORT || 6379,
            password: process.env.REDIS_PASS || undefined
        }
    }
}
```

Microservicio: `mailing-ms`

```typescript
// apps/mailing-ms/src/main.ts
async function bootstrap() {
  const app = await NestFactory.createMicroservice(MailingMsModule, getMicroserviceOptions());
  await app.listen();
}
```

Microservicio: `music-discovery-ms`

```typescript
// apps/music-discovery-ms/src/main.ts
async function bootstrap() {
  
  const app = await NestFactory.create(MusicDiscoveryMsModule);
  app.useGlobalPipes(new ValidationPipe())
  app.connectMicroservice(getMicroserviceOptions())
// other features...
  await app.listen(port, () => {
    Logger.log(`Music discovery microservice listen on port: ${port}`, "Main")
  });
  
}
```

Finalmente, definimos los controladores con su message pattern y ejecutar la lógica de negocio que queramos.

Envío de email de bienvenida al crearse un usuario en el microservicio `mailing-ms`.

```typescript
// apps/mailing-ms/src/integration-events/controllers/integration.controller.ts
@Controller()
export class IntegrationController {
  
  constructor(private readonly email: EmailService) {}

  @MessagePattern('com.clonespotify.accounts.users.integration.user-updated')
  onUserCreated(@Payload() data: UserCreatedEvent, @Ctx() context: RmqContext) {
    Logger.log(`Event received: ${data.name} from ${data.service}`, 'QueueController')
    this.email.notifyUserDetails(data);
  }

}
```

Creación del catálogo inicial del usuario al crearse un nuevo usuario en el microservicio `music-discovery-ms`

```typescript
// apps/music-discovery-ms/src/user-catalog/infrastructure/integration-events/integration.controller.ts
@Controller()
export class IntegrationController {

    constructor(private readonly catalog: UserCatalogUseCases) {}

    @MessagePattern('com.clonespotify.accounts.users.integration.user-updated')
    onUserCreated(@Payload() event: UserCreatedEvent, @Ctx() context: RedisContext) {
        Logger.log(`Event received: ${event.name} from ${event.service}`, 'IntegrationController')
        this.catalog.createMusicCatalog({
            id: Model.generateUUID(),
            user: {
                id: event.payload.id,
                username: event.payload.username
            }
        })
    }
}
```

Finalmente, para ver el ejemplo funcionando, ejecuta lo siguiente.

```bash
npm run start:infra
npm run start:accounts
npm run start:mailing
npm run start:music-discovery
```

Y envía un curl a `accounts-ms`.

```bash
curl -X POST -H "Content-Type: application/json" -d '{
  "id": "12345678-1234-1234-1234-123456789abc",
  "username": "john_doe",
  "password": "password123",
  "email": "john.doe@example.com"
}' http://localhost:3013/users
```

Finalmente, verás los logs de la aplicación.

![example](assets/img/examples/domain-event-vs-integration-event.webp)

## Conclusión

Exploramos los eventos de dominio y de integración con un enfoque práctico y fácil de entender. Los eventos de integración nos ayudan a crear sistemas totalmente desacoplados entre sí, y los eventos de dominio nos ayudan a modelar de mejor manera la lógica de negocio, creando un código totalmente desacoplado y con la capacidad de ser mantenible en el tiempo.

## [Github repository](https://github.com/nullpointer-excelsior/microservices-architecture-nestjs/)


![meme](assets/img/memes/meme2.webp)
