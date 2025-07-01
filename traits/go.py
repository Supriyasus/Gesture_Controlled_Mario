from pygame.transform import flip

class GoTrait:
    def __init__(self, animation, screen, camera, ent):
        self.animation = animation
        self.direction = 0
        self.heading = 1
        self.accelVel = 0.6  # Slightly faster acceleration
        self.decelVel = 0.25
        self.maxVel = 3.0
        self.screen = screen
        self.boost = False
        self.camera = camera
        self.entity = ent

    def update(self):
    # === BOOST MODE LOGIC ===
        if self.boost:
            self.maxVel = 6.0
            self.animation.deltaTime = 3
            print("[DEBUG] BOOST is active! Max speed set to:", self.maxVel)

            # FORCE boost speed directly
            if self.direction != 0:
                self.entity.vel.x = self.maxVel * self.direction
                print("[DEBUG] FORCE boost velocity:", self.entity.vel.x)
        else:
            self.maxVel = 3.2
            self.animation.deltaTime = 7

        # === MOVEMENT ===
        if self.direction != 0:
            self.heading = self.direction

            # Accelerate forward
            target_speed = self.maxVel * self.heading
            if abs(self.entity.vel.x) < abs(target_speed):
                self.entity.vel.x += self.accelVel * self.heading
                if abs(self.entity.vel.x) > abs(target_speed):
                    self.entity.vel.x = target_speed

            # Update animation
            if not self.entity.inAir:
                self.animation.update()
            else:
                self.animation.inAir()
        else:
            # No direction — slow down
            self.animation.update()
            if self.entity.vel.x > 0:
                self.entity.vel.x -= self.decelVel
                if self.entity.vel.x < 0:
                    self.entity.vel.x = 0
            elif self.entity.vel.x < 0:
                self.entity.vel.x += self.decelVel
                if self.entity.vel.x > 0:
                    self.entity.vel.x = 0

            if self.entity.inAir:
                self.animation.inAir()
            else:
                self.animation.idle()

        # === DRAW ===
        if (self.entity.invincibilityFrames // 2) % 2 == 0:
            self.drawEntity()


    def updateAnimation(self, animation):
        self.animation = animation
        self.update()

    def drawEntity(self):
        if self.heading == 1:
            self.screen.blit(self.animation.image, self.entity.getPos())
        else:
            self.screen.blit(flip(self.animation.image, True, False), self.entity.getPos())
