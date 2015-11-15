from PIL import Image, ImageFile
from PIL.GifImagePlugin import getheader, getdata
import binascii
import collections
import logging

def intToBin(i):
    """ Integer to two bytes """
    # devide in two parts (bytes)
    i1 = i % 256
    i2 = int( i/256)
    # make string (little endian)
    return chr(i1) + chr(i2)

def binaryHexlify(string):
    s = binascii.hexlify(string)
    s2 = ''
    for i in xrange(0, len(s)):
        s2 += s[i]
        if i%2 == 1:
            s2 += ' '
    # print s2
    return s2

def getheaderAnim(im):
    """ getheaderAnim(im)
    
    Get animation header. To replace PILs getheader()[0] 
    
    """
    bb = "GIF89a"
    bb += intToBin(im.size[0])
    bb += intToBin(im.size[1])
    bb += "\xF7\x00\x00"
    return bb

def getAppExt(loops=0):
    """ getAppExt(loops=float('inf'))
    
    Application extention. This part specifies the amount of loops.
    If loops is 0, it goes on infinitely.
    
    """
    # (the extension interprets zero loops
    # to mean an infinite number of loops)
    # Mmm, does not seem to work
    if loops == 0:
        loops = 2**16-1
        
    bb = "\x21\xFF\x0B"  # application extension
    bb += "NETSCAPE2.0"
    bb += "\x03\x01"
    bb += intToBin(loops)
    bb += '\x00'  # end
    return bb

def getGraphicsControlExt(duration=0.1, dispose=2, transparent_flag=0, transparency_index=0):
    """ getGraphicsControlExt(duration=0.1, dispose=2)
    
    Graphics Control Extension. A sort of header at the start of
    each image. Specifies duration and transparancy. 
    
    Dispose
    -------
      * 0 - No disposal specified.
      * 1 - Do not dispose. The graphic is to be left in place.
      * 2 - Restore to background color. The area used by the graphic 
        must be restored to the background color.
      * 3 - Restore to previous. The decoder is required to restore the
        area overwritten by the graphic with what was there prior to 
        rendering the graphic.
      * 4-7 -To be defined. 
    
    """
    
    bb = '\x21\xF9\x04'
    bb += chr(((dispose & 3) << 2)|(transparent_flag & 1))  # low bit 1 == transparency,
    # 2nd bit 1 == user input , next 3 bits, the low two of which are used,
    # are dispose.
    bb += intToBin(int(duration*100))
    bb += chr(transparency_index)
    bb += '\x00'  # end
    return bb

def getImageDescriptor(im, xy=None, local=False):
    """ getImageDescriptor(im, xy=None)
    
    Used for the local color table properties per image.
    Otherwise global color table applies to all frames irrespective of
    whether additional colors comes in play that require a redefined
    palette. Still a maximum of 256 color per frame, obviously.
    
    Written by Ant1 on 2010-08-22
    Modified by Alex Robinson in Janurari 2011 to implement subrectangles.
    
    """
    # Defaule use full image and place at upper left
    if xy is None:
        xy  = (0,0)
    
    # Image separator,
    bb = '\x2C' 
    
    # Image position and size
    bb += intToBin(xy[0]) # Left position
    bb += intToBin(xy[1]) # Top position
    bb += intToBin(im.size[0]) # image width
    bb += intToBin(im.size[1]) # image height
    
    # packed field: local color table flag1, interlace0, sorted table0, 
    # reserved00, lct size111=7=2^(7+1)=256.
    bb += '\xC7' if local else '\x40'
    
    # LZW minimum size code now comes later, begining of [image data] blocks
    return bb

def writeGifToFile(fp, images, durations, loops, xys, disposes):
    """ writeGifToFile(fp, images, durations, loops, xys, disposes)
    
    Given a set of images writes the bytes to the specified stream.
    
    """
    palettes = []
    occur = collections.Counter()

    for im in images:
        # palettes.append( getheader(im)[0][-1] )
        p = getheader(im)[1]
        if not p:
            # Appengine development
            p =  getheader(im)[0][-1]
        occur[p] += 1
        palettes.append(p)

    globalPalette = None
    largest = 0
    for p in occur:
        if occur[p] > largest:
            largest = occur[p]
            globalPalette = p
    # print globalPalette
    # print largest

    # Init
    frames = 0
    firstFrame = True
    
    for im, palette in zip(images, palettes):
        if firstFrame:
            # Write header
            # Gather info
            header = getheaderAnim(im)
            appext = getAppExt(loops)

            fp.write(header)
            fp.write(globalPalette)
            fp.write(appext)
            firstFrame = False

        # Write palette and image data
        graphext = getGraphicsControlExt(durations[frames], dispose=2)

        # Write local header
        if (palette != globalPalette) or (disposes[frames] != 2):
            # Use local color palette
            # Make image descriptor suitable for using 256 local color palette
            imdes = getImageDescriptor(im, xys[frames], local=True)
            fp.write(graphext)
            fp.write(imdes) # write suitable image descriptor
            fp.write(palette) # write local color table
        else:
            # Use global color palette
            imdes = getImageDescriptor(im, xys[frames], local=False)
            # print '2', binaryHexlify(imdes2)
            fp.write(graphext)
            fp.write(imdes) # write suitable image descriptor
        fp.write('\x08') # LZW minimum size code
            
        im.encoderinfo = {}
        im.encoderconfig = (8, 1)
        ImageFile._save(im, fp, [("gif", (0, 0)+im.size, 0, 'P')])
        fp.write("\x00")  # end of image data
            
        # Prepare for next round
        frames = frames + 1
    
    fp.write(";")  # end gif
    return frames

def paletteImage(palette):
    """ PIL weird interface for making a paletted image: create an image which
        already has the palette, and use that in Image.quantize. This function
        returns this palette image. """
    # a palette image to use for quant
    pimage = Image.new("P", (1, 1), 0)
    pimage.putpalette(palette)
    return pimage

def gif2gif(img, fp):
    # img = Image.open('chibi_sonic__animated__by_blue_chica-d68050h.gif')
    # duration = img.info['duration']
    # print img.info
    # print img.size
    # print img.tell()
    # base_im = Image.new("RGB", img.size, (255,255,255))
    # base_im.paste(img)
    
    seq = []
    durations = []
    xys = []
    disposes = []
    i = 0
    c = 0
    try:
        while 1:
            # print img.getpalette() == palette
            # palette = img.getpalette()
            # img.putpalette(palette)
            # new_img = Image.new('RGBA', img.size)
            # new_img.paste(img)
            # new_img.save('x'+str(i)+'.png')
            # print img.info
            nim = Image.new("RGB", img.size, (255,255,255))
            # nim.paste(base_im)
            nim.paste(img)
            nim = nim.resize((128, 128), Image.NEAREST)
            # nim.save('x'+str(i)+'.png')
            nim = nim.quantize(palette=paletteImage(img.getpalette()))
            seq.append(nim)
            logging.info(img.info)
            try:
                durations.append(img.info['duration']/1000.0)
            except Exception:
                durations.append(0.1)
            xys.append((0,0))
            disposes.append(2)

            i += 1
            img.seek(img.tell()+1)
    except EOFError:
        pass
    
    # fp = open('out.gif', 'wb')
    writeGifToFile(fp, seq, durations=durations, loops=0, xys=xys, disposes=disposes)
    fp.close()
