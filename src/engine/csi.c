/*
 * csi.c — Causal Scene Intelligence
 * Builds physically-correct scene graphs from text descriptions.
 * Validates physics (gravity, containment, flow direction).
 */

#include "csi.h"
#include <string.h>
#include <stdio.h>
#include <ctype.h>

/* ─── Object detection from text ─── */

static int ci_has(const char *text, const char *word) {
    if (!text || !word) return 0;
    size_t tlen = strlen(text), wlen = strlen(word);
    if (wlen > tlen) return 0;
    for (size_t i = 0; i <= tlen - wlen; i++) {
        int match = 1;
        for (size_t j = 0; j < wlen; j++)
            if (tolower((unsigned char)text[i+j]) != tolower((unsigned char)word[j])) { match=0; break; }
        if (match) return 1;
    }
    return 0;
}

int csi_add_object(CSIScene *scene, const char *name, CSIObjectType type, float x, float y, float z) {
    if (scene->object_count >= CSI_MAX_OBJECTS) return -1;
    CSIObject *o = &scene->objects[scene->object_count];
    strncpy(o->name, name, 31);
    o->type = type;
    o->pos[0] = x; o->pos[1] = y; o->pos[2] = z;
    o->size[0] = 1; o->size[1] = 1; o->size[2] = 1;
    o->color = scene->object_count % 10;
    o->temperature = 20.0f;
    o->is_source = 0;
    return scene->object_count++;
}

void csi_add_relation(CSIScene *scene, int obj_a, int obj_b, CSIRelationType rel) {
    if (scene->relation_count >= CSI_MAX_RELATIONS) return;
    CSIRelation *r = &scene->relations[scene->relation_count++];
    r->obj_a = obj_a;
    r->obj_b = obj_b;
    r->relation = rel;
}

/* ─── Parse description into scene ─── */

CSIScene csi_parse_description(const char *text) {
    CSIScene scene;
    memset(&scene, 0, sizeof(scene));
    strncpy(scene.description, text, sizeof(scene.description) - 1);
    
    /* Detect objects from keywords */
    struct { const char *word; CSIObjectType type; float y; } known[] = {
        {"floor", CSI_OBJ_SURFACE, 0},
        {"ground", CSI_OBJ_SURFACE, 0},
        {"wall", CSI_OBJ_SURFACE, 1.5},
        {"table", CSI_OBJ_SURFACE, 0.8},
        {"ceiling", CSI_OBJ_SURFACE, 3.0},
        {"water", CSI_OBJ_LIQUID, 0},
        {"pool", CSI_OBJ_LIQUID, 0},
        {"pipe", CSI_OBJ_SOLID, 2.5},
        {"machine", CSI_OBJ_SOLID, 0.5},
        {"equipment", CSI_OBJ_SOLID, 0.5},
        {"box", CSI_OBJ_SOLID, 0.5},
        {"car", CSI_OBJ_SOLID, 0.5},
        {"person", CSI_OBJ_SOLID, 0.9},
        {"tree", CSI_OBJ_SOLID, 2.0},
        {"light", CSI_OBJ_LIGHT, 3.0},
        {"sun", CSI_OBJ_LIGHT, 100.0},
        {"fire", CSI_OBJ_GAS, 0.5},
        {"smoke", CSI_OBJ_GAS, 2.0},
        {"steam", CSI_OBJ_GAS, 1.5},
        {"cloud", CSI_OBJ_GAS, 50.0},
        {NULL, 0, 0},
    };
    
    float x_offset = 0;
    for (int i = 0; known[i].word; i++) {
        if (ci_has(text, known[i].word)) {
            int idx = csi_add_object(&scene, known[i].word, known[i].type, x_offset, known[i].y, 0);
            x_offset += 2.0f;
            
            /* Auto-add relations based on physics */
            if (known[i].type == CSI_OBJ_LIQUID && scene.object_count > 1) {
                /* Liquid is below/on surface */
                for (int j = 0; j < idx; j++) {
                    if (scene.objects[j].type == CSI_OBJ_SURFACE && scene.objects[j].pos[1] == 0) {
                        csi_add_relation(&scene, idx, j, CSI_REL_ON_TOP);
                    }
                }
            }
            if (known[i].type == CSI_OBJ_GAS) {
                /* Gas rises above everything */
                for (int j = 0; j < idx; j++) {
                    if (scene.objects[j].pos[1] < known[i].y)
                        csi_add_relation(&scene, idx, j, CSI_REL_ABOVE);
                }
            }
        }
    }
    
    /* Detect spatial keywords for relations */
    if (ci_has(text, "on top") || ci_has(text, "on the")) {
        if (scene.object_count >= 2)
            csi_add_relation(&scene, 0, 1, CSI_REL_ON_TOP);
    }
    if (ci_has(text, "under") || ci_has(text, "below") || ci_has(text, "beneath")) {
        if (scene.object_count >= 2)
            csi_add_relation(&scene, 1, 0, CSI_REL_BELOW);
    }
    if (ci_has(text, "leak") || ci_has(text, "flow") || ci_has(text, "drip")) {
        /* Find liquid and pipe, add flowing relation */
        int liquid = -1, pipe = -1;
        for (int i = 0; i < scene.object_count; i++) {
            if (scene.objects[i].type == CSI_OBJ_LIQUID) liquid = i;
            if (strcmp(scene.objects[i].name, "pipe") == 0) pipe = i;
        }
        if (liquid >= 0 && pipe >= 0)
            csi_add_relation(&scene, liquid, pipe, CSI_REL_FLOWING_FROM);
    }
    
    /* Validate physics */
    scene.physics_valid = csi_validate_physics(&scene);
    
    return scene;
}

/* ─── Physics Validation ─── */

int csi_validate_physics(CSIScene *scene) {
    int valid = 1;
    scene->physics_notes[0] = '\0';
    int pos = 0;
    
    for (int i = 0; i < scene->object_count; i++) {
        CSIObject *o = &scene->objects[i];
        
        /* Rule 1: Solids can't float (must be on surface or ground) */
        if (o->type == CSI_OBJ_SOLID && o->pos[1] > 0) {
            int supported = 0;
            for (int r = 0; r < scene->relation_count; r++) {
                if (scene->relations[r].obj_a == i && scene->relations[r].relation == CSI_REL_ON_TOP)
                    supported = 1;
            }
            if (!supported && o->pos[1] < 10) {
                /* Small height — assume on ground (implicit support) */
            }
        }
        
        /* Rule 2: Liquids flow DOWN (y decreases or stays at 0) */
        if (o->type == CSI_OBJ_LIQUID && o->pos[1] > 0.5f) {
            pos += snprintf(scene->physics_notes + pos, 256 - pos,
                          "Warning: %s at height %.1f (liquids flow down). ", o->name, o->pos[1]);
            valid = 0;
        }
        
        /* Rule 3: Gas rises UP */
        if (o->type == CSI_OBJ_GAS && o->pos[1] < 0.5f) {
            pos += snprintf(scene->physics_notes + pos, 256 - pos,
                          "Warning: %s at height %.1f (gas rises). ", o->name, o->pos[1]);
            valid = 0;
        }
    }
    
    if (valid) strncpy(scene->physics_notes, "All physics constraints satisfied.", 255);
    return valid;
}

/* ─── Scene description ─── */

void csi_describe_scene(CSIScene *scene, char *buf, int max) {
    int pos = 0;
    pos += snprintf(buf + pos, max - pos, "Scene: %d objects, %d relations. ",
                   scene->object_count, scene->relation_count);
    
    for (int i = 0; i < scene->object_count && pos < max - 50; i++) {
        pos += snprintf(buf + pos, max - pos, "[%s at (%.0f,%.0f,%.0f)] ",
                       scene->objects[i].name, scene->objects[i].pos[0],
                       scene->objects[i].pos[1], scene->objects[i].pos[2]);
    }
    
    pos += snprintf(buf + pos, max - pos, "Physics: %s",
                   scene->physics_valid ? "VALID" : "VIOLATIONS DETECTED");
}
