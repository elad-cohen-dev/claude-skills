# NestJS Review Checklist

Framework-specific review checklist for NestJS code.
Apply this checklist when reviewing PRs that contain NestJS controllers, services, modules, or DTOs.

## Checklist

For each item, report **PASS**, **FAIL**, or **N/A**. Explain every FAIL and provide a corrected snippet.

### Architecture
- [ ] Feature-module layout is followed (`features/<name>/<name>.module.ts`)
- [ ] Controllers contain only HTTP concerns — no business logic
- [ ] Business logic lives in services
- [ ] Repositories used for data-access concerns
- [ ] Modules import only what the feature needs — no dumping into `AppModule`

### DTOs & Validation
- [ ] All request bodies use DTOs with `class-validator` decorators
- [ ] Global `ValidationPipe` enabled with `{ whitelist: true, forbidNonWhitelisted: true, transform: true }`
- [ ] Entities are never directly exposed in responses
- [ ] Every DTO property has appropriate validation decorators (`@IsEmail()`, `@IsString()`, `@MinLength()`, etc.)

### Configuration
- [ ] Uses `@nestjs/config` with a typed `ConfigService`
- [ ] `process.env` is never read directly outside config files
- [ ] Env variables validated at startup (Joi or `class-validator`) — fail fast on missing vars

### Security
- [ ] `helmet()` used in `main.ts`
- [ ] `compression()` used in `main.ts`
- [ ] Passwords hashed with `bcrypt` or `argon2` — never stored plain text
- [ ] Auth guards protect sensitive endpoints
- [ ] No mass assignment vulnerabilities (validation pipe whitelists properties)

### Error Handling
- [ ] NestJS `HttpException` subclasses thrown (`NotFoundException`, `BadRequestException`, etc.) — not raw `Error`
- [ ] A global exception filter normalizes error responses
- [ ] Stack traces not exposed in production responses

### Testing
- [ ] Unit tests exist for services
- [ ] Dependencies are properly mocked using Jest
- [ ] `@nestjs/testing` (`Test.createTestingModule`) used for integration tests
- [ ] Test files co-located and named `*.spec.ts`

## Correct Feature Module Example

```typescript
// users.module.ts
@Module({
  imports: [TypeOrmModule.forFeature([User])],
  controllers: [UsersController],
  providers: [UsersService],
  exports: [UsersService],
})
export class UsersModule {}

// users.controller.ts
@Controller('users')
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Get(':id')
  findOne(@Param('id', ParseUUIDPipe) id: string) {
    return this.usersService.findOne(id);
  }
}

// create-user.dto.ts
export class CreateUserDto {
  @IsEmail()
  email: string;

  @IsString()
  @MinLength(8)
  password: string;
}
```
