---
title: "Estrategias de manejo del estado: separando la lógica de negocio y la interfaz de usuario"
author: Benjamin
date: 2025-04-01 00:00:00 -0500
categories: Angular,Frontend,Typescript,Architecture,Coding
tags: Angular,Frontend,Typescript,Architecture,Coding
---

![intro](assets/img/intros/intro13.webp)

La gestión del estado en aplicaciones Angular complejas puede ser un desafío. Aunque NgRx es la opción más popular, su verbosidad y complejidad pueden desanimar a los desarrolladores. Por el contrario, [NGXS](https://www.ngxs.io/) ofrece una alternativa más accesible, permitiendo desde un uso sencillo hasta implementaciones avanzadas, lo que facilita arquitecturas frontend escalables y menos propensas a errores.

## NGXS: ¿Por Qué Elegirlo?

[NGXS](https://www.ngxs.io/) es una biblioteca de gestión de estado para Angular que adopta el patrón de arquitectura Redux pero con un enfoque más ligero y amigable. Esto simplifica el manejo del estado global, al tiempo que permite un flujo de datos unidireccional y predecible, esencial para aplicaciones mantenibles y escalables.

### Ventajas

* **Manejo de estado simplificado:** NGXS integra perfectamente la inyección de dependencias, lo que no solo simplifica la gestión del estado sino que también mejora la mantenibilidad del código.
  
* **Flujo de datos predecible:** Al seguir los principios de Redux, NGXS promueve un flujo de datos unidireccional, lo que facilita el seguimiento y la depuración del estado a lo largo del ciclo de vida de la aplicación.

* **Menos código boilerplate:** Comparado con otras librerías de gestión de estado, NGXS reduce considerablemente la cantidad de código repetitivo, lo que permite a los desarrolladores centrarse más en la lógica de negocio.

* **Curva de aprendizaje suave:** NGXS es más accesible para los nuevos desarrolladores en comparación con NgRx. Su diseño intuitivo permite una adopción progresiva de conceptos más complejos, facilitando la transición de aplicaciones de pequeño a gran tamaño.

* **Soporte para signals:** NGXS Usa tanto Observables como signals de una manera sencilla.

### Desventajas

* **Complejidad en aplicaciones simples:** En aplicaciones más pequeñas y con estados sencillos, la implementación de NGXS puede parecer excesiva. Para algunos proyectos, una gestión de estado más simple podría ser suficiente, y NGXS podría introducir una complejidad innecesaria.

* **Menos popularidad:** A pesar de sus ventajas, NGXS tiene una comunidad y un ecosistema más pequeños en comparación con NgRx. Esto puede limitar el acceso a recursos, herramientas y soporte comunitario.

## La Complejidad del Estado: La Importancia de la Separación de Responsabilidades

Cuando las acciones relacionadas con la lógica de dominio y las acciones relacionadas con la interfaz de usuario (UI) se mezclan, el estado puede volverse complejo e inmanejable. Esta contaminación de la lógica principal dificulta el mantenimiento y la escalabilidad de aplicaciones complejas.

## Estudio de Caso: Checkout APP, Un Frontend Desafiante

Una aplicación de checkout es un ejemplo clásico de una aplicación frontend compleja debido a su infinidad de estados, flujos y bifurcaciones. Dependiendo de las acciones del usuario y las condiciones dadas, la aplicación debe manejar múltiples estados y transiciones.

## Separando Lógicas: UI y Checkout de Manera Eficiente

Para mantener la aplicación de checkout manejable, es crucial separar la lógica de negocio del flujo de navegación de la UI. Esto se logra escuchando las acciones y realizando el flujo de navegación en un componente principal, desacoplando así la arquitectura.

### Flujo de Lógica en el Proceso de Checkout

Las acciones definidas en los estados de NGXS modifican el estado y la lógica del proceso de checkout, incluyendo las partes relacionadas con el pago, el envío y la actualización del carrito. Por ejemplo, la acción `CreatePurchaseAction` en `checkout.actions.ts` y su manejo en `checkout.state.ts` se encarga de realizar la compra y modificar el estado de la compra.

#### ConfirmComponent

```typescript
// confirm.component.ts
@Component({
    ...
})
export class ConfirmationComponent {

  // injecting Store
  private store = inject(Store);
  
  onConfirm() {
    this.store.dispatch(new CreatePurchaseAction({
      ...// action payload
    }))
  }

}
```

#### Checkout state
```typescript
// checkout.state.ts
@State<CheckoutModel>({
    name: 'checkout',
    defaults: {
        purchase: {
            // purchase props
        }
    }
})
@Injectable()
export class CheckoutState {

    private ecommerce = inject(EcommerceApi);

    @Action(CreatePurchaseAction)
    createPurchase(ctx: StateContext<CheckoutModel>, action: CreatePurchaseAction) {
        // executing business service
        return this.ecommerce.processPurchase(action.purchase).pipe(
            tap(res => ctx.patchState({
                purchase: {
                    id: res.purchaseId,
                    ...action.purchase
                }
            }))
        )
    }

    @Selector()
    static getPurchase(state: CheckoutModel) {
        return state.purchase
    }
}
```


### Flujo de Navegación Separado: Garantizando Mantenibilidad y Eficiencia

Para el flujo de navegación, se decide escuchar las acciones y realizar el flujo en un componente principal `checkout-steps-component`, creando así una arquitectura desacoplada. Por ejemplo, el componente `checkout-steps.component.ts` escucha la acción `SetBillingAction` y, dependiendo del estado del pago, navega a la siguiente etapa.

```ts
// checkout-steps.component.ts
@Component()
export class CheckoutStepsComponent implements OnInit {
  
  private store = inject(Store);
  private actions$ = inject(Actions);
  private router = inject(Router);
  private toastr = inject(ToastrService)

  ngOnInit(): void {
    // succesfully purchase step flow
    this.actions$
        .pipe(
            ofActionDispatched(SetBillingAction), // listen action dispatched
            tap(() => this.store.dispatch(new StartLoadingStepAction('Validating your payment method...'))),
            mergeMap(() => this.actions$.pipe(
                ofActionSuccessful(SetBillingAction),// listen action processed succesfully by CheckoutState 
                take(1)
            )),
            untilDestroyed(this),
            map(() => this.store.selectSnapshot(CheckoutState.getPaymentMethodStatus))
        )
        .subscribe(status => {
            if (status === 'accepted') {
                this.store.dispatch(new SetCurrentStepAction(3))
                // routing
                this.router.navigate(['/confirmation'])
            } else {
                this.toastr.error('Payment method not valid')
            }
        })
    // stop loading steps
    this.actions$
      .pipe(ofActionCompleted(SetBillingAction, CreatePurchaseAction), untilDestroyed(this))
      .subscribe(res => this.store.dispatch(new StopLoadingStepAction()))
    // handle errors
    this.actions$
      .pipe(ofActionErrored(SetBillingAction), untilDestroyed(this))
      .subscribe(() => this.store.dispatch(new SetErrorStepAction('Error validando metodo de pago')))
    this.actions$
      .pipe(ofActionErrored(CreatePurchaseAction), untilDestroyed(this))
      .subscribe(() => this.store.dispatch(new SetErrorStepAction('Error creando pago')))

  }
}
```

Este enfoque permitirá que los futuros cambios en los pasos, estados y flujo del checkout se realicen de manera rápida y sencilla, sin afectar la lógica de negocio, lo que garantiza un sistema desacoplado y fácil de mantener.En este ejemplo usamos Steps, pero fácilmente se podría migrar a otro estilo de flujo.


### Ejemplo de Flujo Acoplado: Cuidado con el código altamente acoplado

Un ejemplo de cómo no se debe manejar el flujo sería incluir la lógica de navegación directamente en las acciones de la lógica de negocio. Esto acoplaría la lógica de navegación a la lógica de dominio, haciendo que la aplicación sea más difícil de mantener y probar.

```ts
// High coupled code (NOT RECOMMENDED)
@Action(SetBillingAction)
setBilling(ctx: StateContext<CheckoutModel>, action: SetBillingAction) {
    return this.ecommerce.validatePaymentMethod({
        method: action.billing.payment.method,
        details: {
            ...action.billing.payment.details
        }
    }).pipe(
        map(res => res.valid ? 'accepted' : 'failed'),
        tap(methodStatus => {
            ctx.patchState({
                billing: {
                    ...action.billing,
                    payment: {
                        ...action.billing.payment,
                        methodStatus
                    },
                }
            });
            if(methodStatus === 'accepted'){
                // steps flow !!
                ctx.dispatch(new SetCurrentStepAction(3))
                // routing!!
                this.router.navigate(['/confirmation'])
            }
        })
    )
}
```

La principal desventaja de este enfoque es que la lógica de navegación está directamente acoplada a la lógica de negocio, lo que dificulta la reutilización y el mantenimiento del código.

## Conclusión

Modificar el estado no es la única opción que nos ofrecen las librerías de gestión de estado. También podemos reaccionar a las acciones y realizar flujos alternativos, los cuales nos ayudan a desacoplar las lógicas relacionadas con el proceso principal. 
Esto permite una arquitectura más flexible y mantenible, especialmente en aplicaciones complejas como los procesos de compras. No existe un estándar ni un límite respecto a las opciones que ofrecen estas aplicaciones de tipo 'checkout'; todo depende de las opciones de pago, promociones, tipos de productos, regulaciones o el país donde se realizan las compras. En estos escenarios, utilizar un enfoque reactivo, donde escuchamos acciones sin modificar la lógica principal, se convierte en un gran acierto.

## [Github repository](https://github.com/nullpointer-excelsior/spring-scalable-architectures/tree/master/checkout-frontend)

![meme](assets/img/memes/meme11.webp)

