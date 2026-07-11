#ifndef CSI_H
#define CSI_H

#include <stdint.h>

/*
 * CSI — Causal Scene Intelligence
 * Text → Scene Graph → Physics validation → Description.
 * No rendering yet (needs GPU) — but builds the CORRECT scene structure.
 * Image generation is on the training device; this builds the logic.
 */

#define CSI_MAX_OBJECTS  32
#define CSI_MAX_RELATIONS 64

typedef enum {
    CSI_OBJ_SOLID,     /* Box, sphere, cylinder */
    CSI_OBJ_LIQUID,    /* Water, pool */
    CSI_OBJ_GAS,       /* Smoke, steam */
    CSI_OBJ_LIGHT,     /* Light source */
    CSI_OBJ_SURFACE,   /* Floor, wall, table */
} CSIObjectType;

typedef struct {
    char name[32];
    CSIObjectType type;
    float pos[3];         /* x, y, z */
    float size[3];        /* width, height, depth */
    int color;            /* 0-9 palette index */
    float temperature;    /* For physics simulation */
    int is_source;        /* Is this a cause of something? */
} CSIObject;

typedef enum {
    CSI_REL_ON_TOP,
    CSI_REL_BELOW,
    CSI_REL_INSIDE,
    CSI_REL_NEXT_TO,
    CSI_REL_ABOVE,
    CSI_REL_CONNECTED,
    CSI_REL_FLOWING_FROM,
    CSI_REL_FALLING,
} CSIRelationType;

typedef struct {
    int obj_a;
    int obj_b;
    CSIRelationType relation;
} CSIRelation;

typedef struct {
    CSIObject objects[CSI_MAX_OBJECTS];
    int object_count;
    CSIRelation relations[CSI_MAX_RELATIONS];
    int relation_count;
    char description[512];
    int physics_valid;    /* 1 if physics checks pass */
    char physics_notes[256];
} CSIScene;

/* API */
CSIScene csi_parse_description(const char *text);
int csi_validate_physics(CSIScene *scene);
void csi_describe_scene(CSIScene *scene, char *buf, int max);
int csi_add_object(CSIScene *scene, const char *name, CSIObjectType type, float x, float y, float z);
void csi_add_relation(CSIScene *scene, int obj_a, int obj_b, CSIRelationType rel);

#endif
